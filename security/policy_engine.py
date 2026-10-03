import logging
import math
import os
from typing import Any, Dict, List, Optional

import yaml

from security.findings import SecurityFinding

logger = logging.getLogger(__name__)

_env_policy_path = os.getenv("SECURITY_POLICY_PATH")
if _env_policy_path and os.path.isfile(_env_policy_path):
    DEFAULT_POLICY_PATH = _env_policy_path
else:
    DEFAULT_POLICY_PATH = os.path.join("config", "security_policy.yaml")
DEFAULT_POLICY_OVERLAY_PATH = os.getenv("SECURITY_POLICY_OVERLAY_PATH")


def _validate_policy_fragment(value: Any, baseline: Any, path: str = "policy") -> None:
    if isinstance(baseline, dict):
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be a mapping.")
        unknown_keys = set(value) - set(baseline)
        if unknown_keys:
            raise ValueError(f"{path} contains unsupported keys: {sorted(unknown_keys)}")
        for key, child in value.items():
            _validate_policy_fragment(child, baseline[key], f"{path}.{key}")
        return
    if isinstance(baseline, list):
        if not isinstance(value, list) or (
            baseline and not all(type(item) is type(baseline[0]) for item in value)
        ):
            raise ValueError(f"{path} must be a list matching the baseline item type.")
        return
    if baseline is not None and not isinstance(value, type(baseline)):
        raise ValueError(f"{path} must have type {type(baseline).__name__}.")


def _merge_policy(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_policy(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_security_policy(
    policy_path: str = DEFAULT_POLICY_PATH,
    overlay_path: Optional[str] = DEFAULT_POLICY_OVERLAY_PATH,
) -> Dict[str, Any]:
    """Load a baseline policy and an optional validated, precedence-based overlay."""
    if not os.path.isfile(policy_path):
        raise FileNotFoundError(f"Security policy file not found: '{policy_path}'")
    try:
        with open(policy_path, "r", encoding="utf-8") as policy_file:
            policy = yaml.safe_load(policy_file)
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Could not load security policy '{policy_path}': {exc}") from exc
    if not isinstance(policy, dict):
        raise ValueError(f"Security policy '{policy_path}' must contain a YAML mapping.")

    if overlay_path:
        if not os.path.isfile(overlay_path):
            raise FileNotFoundError(f"Security policy overlay not found: '{overlay_path}'")
        try:
            with open(overlay_path, "r", encoding="utf-8") as overlay_file:
                overlay = yaml.safe_load(overlay_file)
        except (OSError, yaml.YAMLError) as exc:
            raise ValueError(
                f"Could not load security policy overlay '{overlay_path}': {exc}"
            ) from exc
        if not isinstance(overlay, dict):
            raise ValueError(f"Security policy overlay '{overlay_path}' must be a YAML mapping.")
        _validate_policy_fragment(overlay, policy)
        policy = _merge_policy(policy, overlay)

    return policy


def _evaluate_sa_lifetime(ipsec_config: Dict[str, Any], policy: Dict[str, Any]) -> List[SecurityFinding]:
    """Assess SA lifetime while keeping encrypted IKE_AUTH values unverifiable."""
    lifetime_policy = policy.get("sa_lifetime", {})
    max_seconds = lifetime_policy.get("max_seconds", 28800)
    warn_if_unknown = lifetime_policy.get("warn_if_unknown", True)
    lifetime = ipsec_config.get("sa_lifetime")

    is_numeric = isinstance(lifetime, (int, float)) and not isinstance(lifetime, bool)
    if is_numeric:
        is_numeric = math.isfinite(float(lifetime))

    if not is_numeric:
        if not warn_if_unknown:
            return []
        return [SecurityFinding(
            finding_id="IPSEC-LIFE-001",
            category="SA Lifetime",
            severity="MEDIUM",
            title="SA lifetime is not observable",
            observed="unknown",
            expected=f"At most {max_seconds} seconds",
            recommendation="Verify the configured lifetime from the endpoint policy or an authenticated/decrypted IKE_AUTH exchange.",
            status="not_observable",
        )]

    if float(lifetime) <= float(max_seconds):
        return []

    return [SecurityFinding(
        finding_id="IPSEC-LIFE-001",
        category="SA Lifetime",
        severity="MEDIUM",
        title="SA lifetime exceeds policy maximum",
        observed=f"{lifetime} seconds",
        expected=f"At most {max_seconds} seconds",
        recommendation="Reduce the IKE/IPsec SA lifetime to the configured policy maximum.",
        status="violation",
    )]

def evaluate_ipsec_security(
    ipsec_config: Dict[str, Any],
    policy_path: str = DEFAULT_POLICY_PATH,
    traffic_type: Optional[str] = None,
    overlay_path: Optional[str] = DEFAULT_POLICY_OVERLAY_PATH,
) -> List[SecurityFinding]:
    """
    Evaluate IPsec configuration against editable & context-aware security policy.
    Combines hard cryptographic rules with AI-detected traffic type context.
    """
    policy = load_security_policy(policy_path, overlay_path)
    findings: List[SecurityFinding] = []

    if not ipsec_config.get("detected", False):
        return findings

    findings.extend(_evaluate_sa_lifetime(ipsec_config, policy))

    # 1. Protocol Version Evaluation
    ike_version = ipsec_config.get("ike_version", "unknown")
    if ike_version != "unknown":
        disapproved_vers = policy.get("protocol", {}).get("disapproved_versions", ["IKEv1"])
        if any(d.upper() in ike_version.upper() for d in disapproved_vers):
            findings.append(SecurityFinding(
                finding_id="IPSEC-VER-001",
                category="Protocol Version",
                severity="HIGH",
                title="Deprecated IKE protocol version detected",
                observed=ike_version,
                expected="IKEv2",
                recommendation="Upgrade IPsec connection baseline to use IKEv2."
            ))

    # 2. Encryption Algorithm Evaluation
    enc = str(ipsec_config.get("encryption", "unknown"))
    if enc != "unknown":
        approved_encs = policy.get("encryption", {}).get("approved", [])
        forbidden_encs = policy.get("encryption", {}).get("forbidden", [])

        if any(f in enc.upper() for f in forbidden_encs):
            findings.append(SecurityFinding(
                finding_id="IPSEC-ENC-001",
                category="Encryption",
                severity="HIGH",
                title="Weak or forbidden encryption algorithm detected",
                observed=enc,
                expected=f"Approved encryption ({', '.join(approved_encs)})",
                recommendation="Reconfigure IPsec proposals to use strong encryption algorithms such as AES-256-GCM."
            ))
        elif approved_encs and not any(a.upper() in enc.upper() for a in approved_encs):
            findings.append(SecurityFinding(
                finding_id="IPSEC-ENC-002",
                category="Encryption",
                severity="MEDIUM",
                title="Encryption algorithm does not meet policy baseline",
                observed=enc,
                expected=f"Approved encryption ({', '.join(approved_encs)})",
                recommendation="Update IPsec proposal to align with approved corporate baseline algorithms."
            ))

    # 3. Diffie-Hellman Group Evaluation
    dh = ipsec_config.get("dh_group", "unknown")
    if dh != "unknown":
        try:
            dh_group_num = int(dh)
        except (ValueError, TypeError):
            dh_group_num = None

        approved_dh = policy.get("dh_groups", {}).get("approved", [14, 19, 20, 21, 28])
        forbidden_dh = policy.get("dh_groups", {}).get("forbidden", [1, 2, 5])

        if dh_group_num in forbidden_dh:
            findings.append(SecurityFinding(
                finding_id="IPSEC-DH-001",
                category="Key Exchange",
                severity="HIGH",
                title="Insecure Diffie-Hellman group detected",
                observed=f"Group {dh}",
                expected=f"Approved DH group ({', '.join(map(str, approved_dh))})",
                recommendation="Disable weak DH groups (1, 2, 5) and migrate to Group 14 (2048-bit MODP) or Group 19/20 (ECP)."
            ))
        elif dh_group_num and dh_group_num not in approved_dh:
            findings.append(SecurityFinding(
                finding_id="IPSEC-DH-002",
                category="Key Exchange",
                severity="MEDIUM",
                title="Diffie-Hellman group does not meet policy baseline",
                observed=f"Group {dh}",
                expected=f"Approved DH group ({', '.join(map(str, approved_dh))})",
                recommendation="Configure IPsec IKE SA proposal to use an approved DH group."
            ))

    # 4. PRF / Integrity Evaluation
    prf = str(ipsec_config.get("prf", "unknown"))
    if prf != "unknown":
        forbidden_prf = policy.get("prf", {}).get("forbidden", ["MD5", "SHA1"])
        if any(f in prf.upper() for f in forbidden_prf):
            findings.append(SecurityFinding(
                finding_id="IPSEC-PRF-001",
                category="Integrity",
                severity="HIGH",
                title="Weak PRF algorithm detected",
                observed=prf,
                expected="SHA2-based PRF (e.g. HMAC-SHA2-256 or HMAC-SHA2-384)",
                recommendation="Upgrade PRF transform to HMAC-SHA2-256 or HMAC-SHA2-384."
            ))

    # 5. Smart Context-Aware Traffic Evaluation (AI-informed baseline checks)
    if traffic_type:
        tf_upper = traffic_type.upper()
        tf_baselines = policy.get("traffic_specific_baselines", {})

        if tf_upper in tf_baselines:
            rule = tf_baselines[tf_upper]
            # Check VoIP low-latency requirement
            if "recommended_cipher_type" in rule:
                req_type = rule["recommended_cipher_type"]
                integ = str(ipsec_config.get("integrity", "unknown"))
                if req_type == "AEAD" and "AEAD" not in integ and "GCM" not in enc:
                    findings.append(SecurityFinding(
                        finding_id="IPSEC-CTX-VOIP-001",
                        category="Context-Aware Performance",
                        severity="LOW",
                        title=f"Cipher suite suboptimal for predicted AI traffic ({traffic_type})",
                        observed=f"{enc} ({integ})",
                        expected="AES-GCM (AEAD Cipher)",
                        recommendation=rule.get("reason", "Use AES-GCM for low-latency real-time voice traffic.")
                    ))

            # Check File Transfer PFS requirement
            if "pfs_recommendation" in rule:
                pfs = ipsec_config.get("pfs", "unknown")
                if pfs in ["disabled", False]:
                    findings.append(SecurityFinding(
                        finding_id="IPSEC-CTX-FT-001",
                        category="Context-Aware Security",
                        severity="MEDIUM",
                        title=f"PFS disabled for bulk file transfer traffic ({traffic_type})",
                        observed="PFS Disabled",
                        expected="PFS Enforced (Diffie-Hellman Rekeying)",
                        recommendation=rule.get("reason", "Enforce PFS for high-volume file transfer traffic.")
                    ))

    return findings


def evaluate_policy_as_code_rules(
    ipsec_info: Dict[str, Any],
    policy_path: str = DEFAULT_POLICY_PATH,
    overlay_path: Optional[str] = DEFAULT_POLICY_OVERLAY_PATH,
) -> Dict[str, Any]:
    """Evaluate policy badges from the same baseline/overlay and preserve unknowns."""
    policy = load_security_policy(policy_path, overlay_path)
    rules: List[Dict[str, Any]] = []

    def add_rule(rule_id: str, name: str, category: str, observed: Any, requirement: str,
                 description: str, status: str) -> None:
        rules.append({
            "rule_id": rule_id,
            "name": name,
            "category": category,
            "status": status,
            "observed": observed if observed is not None else "unknown",
            "requirement": requirement,
            "description": description,
        })

    def observed(field: str) -> Any:
        value = ipsec_info.get(field)
        return None if value is None or str(value).strip().lower() in {"", "unknown", "none"} else value

    ike = observed("ike_version")
    allowed_versions = policy.get("protocol", {}).get("approved_versions", [])
    banned_versions = policy.get("protocol", {}).get("disapproved_versions", [])
    ike_text = str(ike).upper() if ike is not None else ""
    ike_status = (
        "WARNING" if ike is None
        else "FAIL" if any(str(item).upper() in ike_text for item in banned_versions)
        else "PASS" if any(str(item).upper() in ike_text for item in allowed_versions)
        else "WARNING"
    )
    add_rule("POL-01", "Protocol Version Modernity", "Protocol Baseline", ike,
             ", ".join(map(str, allowed_versions)) or "Approved IKE version",
             "Unknown values are unverified; known values are checked against the active policy.", ike_status)

    encryption = observed("encryption")
    encryption_text = str(encryption).upper() if encryption is not None else ""
    enc_policy = policy.get("encryption", {})
    enc_forbidden = enc_policy.get("forbidden", [])
    enc_approved = enc_policy.get("approved", [])
    encryption_status = (
        "WARNING" if encryption is None
        else "FAIL" if any(str(item).upper() in encryption_text for item in enc_forbidden)
        else "PASS" if any(str(item).upper() in encryption_text for item in enc_approved)
        else "WARNING"
    )
    add_rule("POL-02", "Encryption Cipher Strength", "Confidentiality", encryption,
             ", ".join(map(str, enc_approved)) or "Approved encryption",
             "Unknown values are unverified; approved and forbidden algorithms come from the active policy.",
             encryption_status)

    dh = observed("dh_group")
    dh_text = str(dh) if dh is not None else ""
    dh_policy = policy.get("dh_groups", {})
    dh_forbidden = {str(item) for item in dh_policy.get("forbidden", [])}
    dh_approved = {str(item) for item in dh_policy.get("approved", [])}
    dh_status = (
        "WARNING" if dh is None
        else "FAIL" if dh_text in dh_forbidden
        else "PASS" if dh_text in dh_approved
        else "WARNING"
    )
    add_rule("POL-03", "Diffie-Hellman Key Agreement", "Key Agreement", dh,
             ", ".join(sorted(dh_approved)) or "Approved key-exchange groups",
             "Unknown values remain unverified; group allowlists come from the active policy.", dh_status)

    pfs = observed("pfs")
    pfs_enabled = pfs is True or str(pfs).lower() in {"enforced", "yes", "true"}
    pfs_required = bool(policy.get("pfs", {}).get("required", True))
    pfs_status = "WARNING" if pfs is None else (
        "PASS" if pfs_enabled or not pfs_required else "FAIL"
    )
    add_rule("POL-04", "Perfect Forward Secrecy", "Key Isolation", pfs,
             "Required" if pfs_required else "Not required",
             "A packet capture that cannot observe a rekey leaves PFS unverified.", pfs_status)

    prf = observed("prf") or observed("integrity")
    prf_text = str(prf).upper() if prf is not None else ""
    prf_policy = policy.get("prf", {})
    prf_forbidden = prf_policy.get("forbidden", [])
    prf_approved = prf_policy.get("approved", [])
    prf_status = (
        "WARNING" if prf is None
        else "FAIL" if any(str(item).upper() in prf_text for item in prf_forbidden)
        else "PASS" if any(str(item).upper() in prf_text for item in prf_approved)
        else "WARNING"
    )
    add_rule("POL-05", "PRF / Integrity Algorithm", "Integrity", prf,
             ", ".join(map(str, prf_approved)) or "Approved PRF / integrity",
             "Unknown values are unverified; algorithm policy is loaded from the active overlay.",
             prf_status)

    mode = observed("mode")
    mode_status = "WARNING" if mode is None else (
        "PASS" if str(mode).lower() == "tunnel" else "WARNING"
    )
    add_rule("POL-06", "Encapsulation Mode", "Network Topology", mode,
             "Tunnel" if mode is not None else "Mode is not observable",
             "An absent mode cannot be treated as compliant.", mode_status)

    replay = observed("replay_protection")
    replay_required = bool(policy.get("replay_protection", {}).get("required", True))
    replay_enabled = replay is True or str(replay).lower() in {"enabled", "yes", "true"}
    replay_status = "WARNING" if replay is None else (
        "PASS" if replay_enabled or not replay_required else "FAIL"
    )
    add_rule("POL-07", "Anti-Replay Configuration", "Packet Protection", replay,
             "Required" if replay_required else "Not required",
             "ESP sequence numbers do not reveal the configured anti-replay window.", replay_status)

    passed = sum(rule["status"] == "PASS" for rule in rules)
    warnings = sum(rule["status"] == "WARNING" for rule in rules)
    failed = sum(rule["status"] == "FAIL" for rule in rules)
    assessed = passed + failed
    return {
        "total_rules": len(rules),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "compliance_score": int((passed / assessed) * 100) if assessed else None,
        "rule_results": rules,
        "policy_name": policy.get("policy_name"),
        "policy_version": policy.get("version"),
        "overlay_applied": bool(overlay_path),
    }
