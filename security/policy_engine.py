import os
import yaml
import logging
from typing import Dict, Any, List, Optional

from security.findings import SecurityFinding

logger = logging.getLogger(__name__)

DEFAULT_POLICY_PATH = os.path.join("config", "security_policy.yaml")

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
        "risk_weights": {"HIGH": 30, "MEDIUM": 15, "LOW": 5}
    }

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
                if pfs == "disabled":
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
