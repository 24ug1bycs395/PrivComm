import os
import math
import yaml
import logging
from typing import Dict, Any, List, Optional

from security.findings import SecurityFinding

logger = logging.getLogger(__name__)

DEFAULT_POLICY_PATH = os.getenv(
    "SECURITY_POLICY_PATH",
    os.path.join("config", "security_policy.yaml"),
)

def load_security_policy(policy_path: str = DEFAULT_POLICY_PATH) -> Dict[str, Any]:
    """Load security policy baseline from YAML file."""
    if os.path.exists(policy_path):
        try:
            with open(policy_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load policy file '{policy_path}': {e}")

    # Fallback policy
    return {
        "encryption": {"approved": ["AES-256-GCM", "AES-128-GCM", "AES-256-CBC"], "forbidden": ["DES", "3DES"]},
        "dh_groups": {"approved": [14, 19, 20, 21, 28], "forbidden": [1, 2, 5]},
        "integrity": {"approved": ["AEAD", "HMAC-SHA2-256", "HMAC-SHA2-384"], "forbidden": ["MD5", "SHA1"]},
        "prf": {"approved": ["HMAC-SHA2-256", "HMAC-SHA2-384", "HMAC-SHA2-512"], "forbidden": ["MD5", "SHA1"]},
        "protocol": {"approved_versions": ["IKEv2"], "disapproved_versions": ["IKEv1"]},
        "risk_weights": {"HIGH": 30, "MEDIUM": 15, "LOW": 5},
        "sa_lifetime": {"max_seconds": 28800, "warn_if_unknown": False}
    }


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
    traffic_type: Optional[str] = None
) -> List[SecurityFinding]:
    """
    Evaluate IPsec configuration against editable & context-aware security policy.
    Combines hard cryptographic rules with AI-detected traffic type context.
    """
    policy = load_security_policy(policy_path)
    findings: List[SecurityFinding] = []

    if not ipsec_config.get("detected", False):
        return findings

    findings.extend(_evaluate_sa_lifetime(ipsec_config, policy))

    # 1. Protocol Version Evaluation
    ike_version = ipsec_config.get("ike_version", "unknown")
    if ike_version != "unknown":
        disapproved_vers = policy.get("protocol", {}).get("disapproved_versions", ["IKEv1"])
        if ike_version in disapproved_vers:
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


def evaluate_policy_as_code_rules(ipsec_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates org-defined Policy-as-Code control rules and produces explicit PASS/WARNING/FAIL badges.
    """
    rules: List[Dict[str, Any]] = []

    # POL-01: Protocol Modernity
    ike_ver = str(ipsec_info.get("ike_version", "IKEv2")).upper()
    if "V2" in ike_ver or ike_ver == "IKEV2":
        rules.append({
            "rule_id": "POL-01",
            "name": "Protocol Version Modernity",
            "category": "Protocol Baseline",
            "status": "PASS",
            "observed": ike_ver,
            "requirement": "IKEv2 Mandatory",
            "description": "IKEv2 stream exchange verified. Resists DoS state exhaustion and supports MOBIKE mobility."
        })
    elif "AGGRESSIVE" in ike_ver:
        rules.append({
            "rule_id": "POL-01",
            "name": "Protocol Version Modernity",
            "category": "Protocol Baseline",
            "status": "FAIL",
            "observed": "IKEv1 Aggressive Mode",
            "requirement": "IKEv2 Mandatory",
            "description": "CRITICAL: Aggressive Mode exposes PSK hashes to offline GPU cracking."
        })
    else:
        rules.append({
            "rule_id": "POL-01",
            "name": "Protocol Version Modernity",
            "category": "Protocol Baseline",
            "status": "WARNING",
            "observed": ike_ver,
            "requirement": "IKEv2 Mandatory",
            "description": "Legacy protocol handshake detected. Migration to IKEv2 required."
        })

    # POL-02: Encryption Cipher Strength
    enc = str(ipsec_info.get("encryption", "AES-256-GCM")).upper()
    if any(forbidden in enc for forbidden in ["3DES", "DES", "NULL", "NONE"]):
        rules.append({
            "rule_id": "POL-02",
            "name": "Encryption Cipher Strength",
            "category": "Confidentiality",
            "status": "FAIL",
            "observed": enc,
            "requirement": "AES-256-GCM / AES-128-GCM / ChaCha20-Poly1305",
            "description": "Prohibited cipher detected. Vulnerable to Sweet32 collision or raw plaintext eavesdropping."
        })
    elif "GCM" in enc or "CHACHA" in enc:
        rules.append({
            "rule_id": "POL-02",
            "name": "Encryption Cipher Strength",
            "category": "Confidentiality",
            "status": "PASS",
            "observed": enc,
            "requirement": "AEAD Cipher Required",
            "description": "Top-tier AEAD cipher providing combined confidentiality and integrated Galois integrity verification."
        })
    else:
        rules.append({
            "rule_id": "POL-02",
            "name": "Encryption Cipher Strength",
            "category": "Confidentiality",
            "status": "WARNING",
            "observed": enc,
            "requirement": "AEAD Cipher Preferred",
            "description": "CBC block mode cipher requires external HMAC integrity checks."
        })

    # POL-03: Diffie-Hellman Key Agreement Margin
    dh = str(ipsec_info.get("dh_group", "19")).upper()
    if dh in ["1", "2", "5", "MODP-1024"]:
        rules.append({
            "rule_id": "POL-03",
            "name": "Diffie-Hellman Cryptographic Margin",
            "category": "Key Agreement",
            "status": "FAIL",
            "observed": f"Group {dh} (1024-bit)",
            "requirement": "Group 14+ or Group 19+",
            "description": "Sub-minimum prime modulus vulnerable to supercomputer precomputation (Logjam attack)."
        })
    elif dh in ["19", "20", "21", "28", "31", "ECP-256", "ECP-384"]:
        rules.append({
            "rule_id": "POL-03",
            "name": "Diffie-Hellman Cryptographic Margin",
            "category": "Key Agreement",
            "status": "PASS",
            "observed": f"Group {dh} (Elliptic Curve)",
            "requirement": "Group 19+ ECP Required",
            "description": "High-speed Elliptic Curve prime group providing 128-bit+ symmetric security margin."
        })
    else:
        rules.append({
            "rule_id": "POL-03",
            "name": "Diffie-Hellman Cryptographic Margin",
            "category": "Key Agreement",
            "status": "PASS" if dh in ["14", "15", "16", "2048"] else "WARNING",
            "observed": f"Group {dh}",
            "requirement": "Group 14+ (2048-bit MODP)",
            "description": "Modular prime group meets NIST enterprise baseline."
        })

    # POL-04: Perfect Forward Secrecy (PFS)
    pfs_val = ipsec_info.get("pfs")
    pfs_enforced = True if pfs_val in [True, "enforced", "yes"] else False
    if pfs_enforced:
        rules.append({
            "rule_id": "POL-04",
            "name": "Perfect Forward Secrecy (PFS)",
            "category": "Key Isolation",
            "status": "PASS",
            "observed": "Enforced",
            "requirement": "CREATE_CHILD_SA Rekeying Mandatory",
            "description": "Ephemeral key generation isolates session keys from master key compromise."
        })
    else:
        rules.append({
            "rule_id": "POL-04",
            "name": "Perfect Forward Secrecy (PFS)",
            "category": "Key Isolation",
            "status": "FAIL",
            "observed": "Disabled",
            "requirement": "PFS Mandatory",
            "description": "Retroactive decryption risk: stealing server master key compromises historical recorded traffic."
        })

    # POL-05: Obsolete Hash Prohibition
    prf = str(ipsec_info.get("prf", ipsec_info.get("integrity", "AEAD"))).upper()
    if any(weak in prf for weak in ["MD5", "SHA1"]):
        rules.append({
            "rule_id": "POL-05",
            "name": "Obsolete Hash Prohibition",
            "category": "Integrity",
            "status": "FAIL",
            "observed": prf,
            "requirement": "MD5 & SHA-1 Prohibited",
            "description": "Legacy hash algorithm vulnerable to cryptographic collision attacks."
        })
    else:
        rules.append({
            "rule_id": "POL-05",
            "name": "Obsolete Hash Prohibition",
            "category": "Integrity",
            "status": "PASS",
            "observed": prf,
            "requirement": "AEAD / SHA2-256+",
            "description": "Compliant hash verification digest."
        })

    # POL-06: Encapsulation Envelope
    mode = str(ipsec_info.get("mode", "Tunnel")).capitalize()
    if mode == "Tunnel":
        rules.append({
            "rule_id": "POL-06",
            "name": "Encapsulation Envelope Protection",
            "category": "Network Topology",
            "status": "PASS",
            "observed": "Tunnel Mode",
            "requirement": "Tunnel Mode Mandatory",
            "description": "Complete packet encapsulation hides internal private IP architecture."
        })
    else:
        rules.append({
            "rule_id": "POL-06",
            "name": "Encapsulation Envelope Protection",
            "category": "Network Topology",
            "status": "WARNING",
            "observed": "Transport Mode",
            "requirement": "Tunnel Mode Preferred",
            "description": "Transport mode leaves original source/destination IP headers visible."
        })

    passed = sum(1 for r in rules if r["status"] == "PASS")
    warnings = sum(1 for r in rules if r["status"] == "WARNING")
    failed = sum(1 for r in rules if r["status"] == "FAIL")

    comp_score = int((passed / len(rules)) * 100) if rules else 100

    return {
        "total_rules": len(rules),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "compliance_score": comp_score,
        "rule_results": rules
    }

