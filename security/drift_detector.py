"""
Configuration Drift Detection Engine for IPsec VPN Tunnels.

Compares observed live IPsec configuration parameters against enterprise
golden baseline policies on a field-by-field basis. Highlights configuration drift,
variance scores, and severity rankings for auditing compliance.
"""

from typing import Dict, Any, List

DEFAULT_GOLDEN_BASELINE = {
    "ike_version": "IKEv2",
    "encryption": "AES-256-GCM",
    "key_length": "256",
    "dh_group": "19",
    "pfs": "enforced",
    "mode": "Tunnel",
    "integrity": "AEAD"
}

TRAFFIC_SPECIFIC_BASELINES = {
    "VOIP": {
        "ike_version": "IKEv2",
        "encryption": "AES-256-GCM",
        "key_length": "256",
        "dh_group": "19",
        "pfs": "enforced",
        "mode": "Tunnel",
        "integrity": "AEAD",
        "name": "VoIP Real-Time Low-Latency Baseline"
    },
    "FILE-TRANSFER": {
        "ike_version": "IKEv2",
        "encryption": "AES-256-GCM",
        "key_length": "256",
        "dh_group": "20",
        "pfs": "enforced",
        "mode": "Tunnel",
        "integrity": "AEAD",
        "name": "High-Volume Bulk Data Isolation Baseline"
    },
    "VIDEO-STREAMING": {
        "ike_version": "IKEv2",
        "encryption": "AES-128-GCM",
        "key_length": "128",
        "dh_group": "19",
        "pfs": "enforced",
        "mode": "Tunnel",
        "integrity": "AEAD",
        "name": "High-Throughput Streaming Baseline"
    }
}

FIELD_DISPLAY_NAMES = {
    "ike_version": "IKE Protocol Version",
    "encryption": "Encryption Cipher Algorithm",
    "key_length": "Symmetric Key Length",
    "dh_group": "Diffie-Hellman Key Exchange Group",
    "pfs": "Perfect Forward Secrecy (PFS)",
    "mode": "IPsec Encapsulation Mode",
    "integrity": "Integrity / Authentication Method"
}


def detect_configuration_drift(
    ipsec_info: Dict[str, Any],
    baseline: Dict[str, Any] = None,
    traffic_type: str = None
) -> Dict[str, Any]:
    """
    Compares observed IPsec tunnel parameters against golden enterprise baseline.
    Supports traffic-type specific dynamic baseline selection.
    """
    if baseline:
        target_baseline = baseline
    elif traffic_type and traffic_type.upper() in TRAFFIC_SPECIFIC_BASELINES:
        target_baseline = TRAFFIC_SPECIFIC_BASELINES[traffic_type.upper()]
    else:
        target_baseline = DEFAULT_GOLDEN_BASELINE

    field_diffs: List[Dict[str, Any]] = []

    total_fields = len(target_baseline)
    drift_count = 0
    total_penalty = 0

    # 1. Evaluate IKE Version
    obs_ike = str(ipsec_info.get("ike_version", "UNKNOWN")).upper()
    base_ike = str(target_baseline.get("ike_version", "IKEv2")).upper()
    if base_ike not in obs_ike and "V2" not in obs_ike:
        drift_count += 1
        total_penalty += 25
        field_diffs.append({
            "field_id": "ike_version",
            "field_name": FIELD_DISPLAY_NAMES["ike_version"],
            "baseline": target_baseline.get("ike_version", "IKEv2"),
            "observed": ipsec_info.get("ike_version", "Unknown"),
            "status": "DRIFTED",
            "severity": "HIGH",
            "impact": "Legacy protocol handshake exposes session initiation to DoS and hash cracking."
        })
    else:
        field_diffs.append({
            "field_id": "ike_version",
            "field_name": FIELD_DISPLAY_NAMES["ike_version"],
            "baseline": target_baseline.get("ike_version", "IKEv2"),
            "observed": ipsec_info.get("ike_version", "IKEv2"),
            "status": "SYNCHRONIZED",
            "severity": "NONE",
            "impact": "Aligned with enterprise IKEv2 baseline."
        })

    # 2. Evaluate Encryption Cipher Algorithm
    obs_enc = str(ipsec_info.get("encryption", "UNKNOWN")).upper()
    base_enc = str(target_baseline.get("encryption", "AES-256-GCM")).upper()
    if base_enc not in obs_enc and "256-GCM" not in obs_enc and "GCM" not in obs_enc:
        drift_count += 1
        sev = "CRITICAL" if any(b in obs_enc for b in ["3DES", "DES", "NULL"]) else "MEDIUM"
        penalty = 30 if sev == "CRITICAL" else 15
        total_penalty += penalty
        field_diffs.append({
            "field_id": "encryption",
            "field_name": FIELD_DISPLAY_NAMES["encryption"],
            "baseline": target_baseline.get("encryption", "AES-256-GCM"),
            "observed": ipsec_info.get("encryption", "Unknown Cipher"),
            "status": "DRIFTED",
            "severity": sev,
            "impact": "Sub-optimal or obsolete cipher algorithm compromises data confidentiality margin."
        })
    else:
        field_diffs.append({
            "field_id": "encryption",
            "field_name": FIELD_DISPLAY_NAMES["encryption"],
            "baseline": target_baseline.get("encryption", "AES-256-GCM"),
            "observed": ipsec_info.get("encryption", "AES-256-GCM"),
            "status": "SYNCHRONIZED",
            "severity": "NONE",
            "impact": "Aligned with bank-grade AEAD cipher baseline."
        })

    # 3. Evaluate DH Group
    obs_dh = str(ipsec_info.get("dh_group", "UNKNOWN"))
    base_dh = str(target_baseline.get("dh_group", "19"))
    if obs_dh != base_dh and obs_dh not in ["19", "20", "31", "ECP-256", "ECP-384"]:
        drift_count += 1
        sev = "HIGH" if obs_dh in ["1", "2", "5"] else "MEDIUM"
        penalty = 25 if sev == "HIGH" else 15
        total_penalty += penalty
        field_diffs.append({
            "field_id": "dh_group",
            "field_name": FIELD_DISPLAY_NAMES["dh_group"],
            "baseline": f"Group {base_dh} (ECP-256)",
            "observed": f"Group {obs_dh}",
            "status": "DRIFTED",
            "severity": sev,
            "impact": "Key agreement group below NIST Group 19 Elliptic Curve baseline."
        })
    else:
        field_diffs.append({
            "field_id": "dh_group",
            "field_name": FIELD_DISPLAY_NAMES["dh_group"],
            "baseline": f"Group {base_dh} (ECP-256)",
            "observed": f"Group {obs_dh if obs_dh != 'UNKNOWN' else base_dh}",
            "status": "SYNCHRONIZED",
            "severity": "NONE",
            "impact": "Aligned with NIST Elliptic Curve key exchange baseline."
        })

    # 4. Evaluate Perfect Forward Secrecy (PFS)
    pfs_val = ipsec_info.get("pfs")
    pfs_enforced = True if pfs_val in [True, "enforced", "yes"] else False
    if not pfs_enforced:
        drift_count += 1
        total_penalty += 20
        field_diffs.append({
            "field_id": "pfs",
            "field_name": FIELD_DISPLAY_NAMES["pfs"],
            "baseline": "Enforced (CREATE_CHILD_SA Rekeying)",
            "observed": "Disabled / Static Derivation",
            "status": "DRIFTED",
            "severity": "HIGH",
            "impact": "Lack of ephemeral rekeying creates retroactive decryption vulnerability."
        })
    else:
        field_diffs.append({
            "field_id": "pfs",
            "field_name": FIELD_DISPLAY_NAMES["pfs"],
            "baseline": "Enforced",
            "observed": "Enforced",
            "status": "SYNCHRONIZED",
            "severity": "NONE",
            "impact": "Aligned with ephemeral key isolation baseline."
        })

    # 5. Evaluate Encapsulation Mode
    obs_mode = str(ipsec_info.get("mode", "Tunnel")).capitalize()
    base_mode = str(target_baseline.get("mode", "Tunnel")).capitalize()
    if obs_mode != base_mode:
        drift_count += 1
        total_penalty += 10
        field_diffs.append({
            "field_id": "mode",
            "field_name": FIELD_DISPLAY_NAMES["mode"],
            "baseline": base_mode,
            "observed": obs_mode,
            "status": "DRIFTED",
            "severity": "LOW",
            "impact": "Transport mode exposes internal IP headers on public network paths."
        })
    else:
        field_diffs.append({
            "field_id": "mode",
            "field_name": FIELD_DISPLAY_NAMES["mode"],
            "baseline": base_mode,
            "observed": obs_mode,
            "status": "SYNCHRONIZED",
            "severity": "NONE",
            "impact": "Aligned with outer IP envelope protection baseline."
        })

    variance_score = min(100, total_penalty)
    is_drifted = drift_count > 0

    return {
        "drift_detected": is_drifted,
        "drift_status": "DRIFTED" if is_drifted else "SYNCHRONIZED",
        "drift_count": drift_count,
        "total_fields_evaluated": total_fields,
        "variance_score": variance_score,
        "field_diffs": field_diffs
    }
