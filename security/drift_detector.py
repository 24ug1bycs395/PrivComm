"""
Configuration Drift Detection Engine for IPsec VPN Tunnels.

Compares observed live IPsec configuration parameters against enterprise
golden baseline policies on a field-by-field basis. Highlights configuration drift,
variance scores, and severity rankings for auditing compliance.
"""

from typing import Any, Dict, List

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
    """Compare known observations with an explicit or reference security baseline."""
    if baseline:
        target_baseline = baseline
    elif traffic_type and traffic_type.upper() in TRAFFIC_SPECIFIC_BASELINES:
        target_baseline = TRAFFIC_SPECIFIC_BASELINES[traffic_type.upper()]
    else:
        target_baseline = DEFAULT_GOLDEN_BASELINE

    field_diffs: List[Dict[str, Any]] = []
    drift_count = 0
    total_penalty = 0
    penalties = {"ike_version": 25, "encryption": 30, "dh_group": 25, "pfs": 20, "mode": 10}
    severities = {"ike_version": "HIGH", "encryption": "HIGH", "dh_group": "HIGH", "pfs": "HIGH", "mode": "LOW"}

    tracked_fields = [
        field for field in target_baseline
        if field in FIELD_DISPLAY_NAMES
    ]
    total_fields = len(tracked_fields)
    for field in tracked_fields:
        baseline_value = target_baseline.get(field)
        observed = ipsec_info.get(field)
        known = (
            observed is not None
            and str(observed).strip().lower() not in {"", "unknown", "none"}
        )
        matches = False
        if known:
            if field in {"pfs"}:
                matches = bool(observed is True or str(observed).lower() in {"enforced", "yes", "true"})
                baseline_bool = bool(
                    baseline_value is True
                    or str(baseline_value).lower() in {"enforced", "yes", "true"}
                )
                matches = matches == baseline_bool
            else:
                matches = str(observed).strip().lower() == str(baseline_value).strip().lower()
        if not known:
            status = "UNVERIFIED"
            severity = "INFO"
            impact = "The observed capture does not reveal this configuration value."
            observed_value = observed if observed is not None else "unknown"
        elif matches:
            status = "SYNCHRONIZED"
            severity = "NONE"
            impact = "Observed value matches the selected reference baseline."
            observed_value = observed
        else:
            status = "DRIFTED"
            severity = severities.get(field, "MEDIUM")
            impact = "Observed value differs from the selected reference baseline."
            observed_value = observed
            drift_count += 1
            total_penalty += penalties.get(field, 10)
        field_diffs.append({
            "field_id": field,
            "field_name": FIELD_DISPLAY_NAMES[field],
            "baseline": baseline_value,
            "observed": observed_value,
            "status": status,
            "severity": severity,
            "impact": impact,
        })

    variance_score = min(100, total_penalty)
    is_drifted = drift_count > 0
    drift_status = "DRIFTED" if is_drifted else (
        "UNVERIFIED"
        if any(item["status"] == "UNVERIFIED" for item in field_diffs)
        else "SYNCHRONIZED"
    )

    return {
        "drift_detected": is_drifted,
        "drift_status": drift_status,
        "drift_count": drift_count,
        "total_fields_evaluated": total_fields,
        "variance_score": variance_score,
        "field_diffs": field_diffs,
        "baseline_source": "explicit" if baseline else (
            "traffic_specific_reference" if traffic_type and traffic_type.upper() in TRAFFIC_SPECIFIC_BASELINES
            else "built_in_reference"
        ),
    }
