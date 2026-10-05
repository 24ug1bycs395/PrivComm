import csv
import json
import logging
import os
from typing import Any, Dict, List

from reports.crypto_bom import build_crypto_bom

logger = logging.getLogger(__name__)

KNOWN_LIMITATIONS = [
    {
        "field": "sa_lifetime",
        "reason": "IKEv2 SA lifetime is negotiated in IKE_AUTH payloads which are encrypted after the IKE_SA_INIT exchange. It cannot be extracted from a PCAP without the pre-shared key or private key for decryption.",
        "status": "not_observable_without_decryption",
    },
    {
        "field": "pfs",
        "reason": "A CREATE_CHILD_SA exchange with a Diffie-Hellman KE payload can be observed in some captures, but its absence does not prove PFS is disabled and its presence does not establish the endpoint's enforcement policy.",
        "status": "enforcement_policy_not_proven_by_capture",
    },
    {
        "field": "replay_protection",
        "reason": "The ESP sequence number is visible in the ESP header, but the configured anti-replay window and enforcement behavior are not established by observing sequence numbers alone.",
        "status": "window_configuration_not_observable_from_sequence_numbers",
    },
]

from security.drift_detector import detect_configuration_drift
from security.explainability import generate_plain_english_explanations
from security.policy_engine import evaluate_policy_as_code_rules
from security.pqc_assessor import evaluate_post_quantum_readiness


def build_unified_analysis_report(
    ingest_res: Dict[str, Any],
    traffic_res: Dict[str, Any],
    findings: List[Any],
    recommendations: List[Dict[str, Any]],
    risk_res: Dict[str, Any]
) -> Dict[str, Any]:
    """Build standardized unified analysis dictionary matching PRD Section 12."""
    ipsec_info = ingest_res.get("ipsec", {})
    meta_exposure = ingest_res.get("metadata_exposure", {})
    explanations = generate_plain_english_explanations(ipsec_info, traffic_res, meta_exposure)
    drift_res = detect_configuration_drift(ipsec_info)
    policy_rules_res = evaluate_policy_as_code_rules(ipsec_info)
    pqc_res = evaluate_post_quantum_readiness(ipsec_info)
    crypto_bom = build_crypto_bom(
        ipsec_info,
        ingest_res.get("capture_sha256"),
        ingest_res.get("packet_evidence", []),
    )
    serialized_findings = []
    for finding in findings:
        item = finding.to_dict() if hasattr(finding, "to_dict") else dict(finding)
        category = str(item.get("category", "")).lower()
        finding_id = str(item.get("finding_id", ""))
        if finding_id.startswith("IPSEC-") or category in {
            "protocol version", "encryption", "key exchange", "integrity",
        }:
            protocol = "ESP" if "replay" in category or "esp" in str(item.get("title", "")).lower() else "IKE"
            item["evidence_references"] = [
                {
                    "frame_number": packet["frame_number"],
                    "timestamp": packet["timestamp"],
                    "protocol": packet["protocol"],
                    "capture_byte_offset": packet["capture_byte_offset"],
                    "capture_byte_length": packet["capture_byte_length"],
                    "evidence_scope": "related packet context; this reference does not prove hidden or unobserved configuration",
                }
                for packet in ingest_res.get("packet_evidence", [])
                if packet.get("protocol") == protocol
            ]
            item["evidence_status"] = (
                "referenced" if item["evidence_references"] else "unavailable"
            )
        serialized_findings.append(item)

    report = {
        "capture": {
            "filename": ingest_res.get("filename", "unknown"),
            "filepath": ingest_res.get("filepath", "unknown"),
            "packet_count": ingest_res.get("packet_count", 0),
            "sha256": ingest_res.get("capture_sha256"),
            "decoder_error": ingest_res.get("decoder_error"),
        },
        "packet_evidence": ingest_res.get("packet_evidence", []),
        "ipsec": ipsec_info,
        "traffic_classification": traffic_res,
        "metadata_exposure": meta_exposure,
        "security_assessment": {
            "risk_score": risk_res.get("score", 0),
            "risk_level": risk_res.get("level", "SECURE"),
            "methodology": risk_res.get("method"),
            "findings_count": len(findings),
            "findings": serialized_findings,
            "recommendations": recommendations,
            "metadata_exposure": meta_exposure
        },
        "explainability": explanations,
        "drift_detection": drift_res,
        "policy_as_code": policy_rules_res,
        "post_quantum_readiness": pqc_res,
        "crypto_bom": crypto_bom,
        "known_limitations": [dict(item) for item in KNOWN_LIMITATIONS],
    }

    return report


def save_json_report(report_data: Dict[str, Any], output_path: str):
    """Save analysis report dictionary to JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=4)
    logger.info(f"Saved analysis report to {output_path}")

def generate_batch_summary_csv(reports_list: List[Dict[str, Any]], csv_path: str):
    """Generate summary CSV for batch processed captures matching PRD Section 14."""
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)

    fieldnames = [
        "capture",
        "ipsec_detected",
        "ike_version",
        "encryption",
        "dh_group",
        "traffic_type",
        "traffic_confidence",
        "risk_level",
        "finding_count"
    ]

    rows = []
    for r in reports_list:
        cap = r.get("capture", {})
        ipsec = r.get("ipsec", {})
        tc = r.get("traffic_classification", {})
        sec = r.get("security_assessment", {})

        row = {
            "capture": cap.get("filename", "unknown"),
            "ipsec_detected": ipsec.get("detected", False),
            "ike_version": ipsec.get("ike_version", "unknown"),
            "encryption": ipsec.get("encryption", "unknown"),
            "dh_group": ipsec.get("dh_group", "unknown"),
            "traffic_type": tc.get("traffic_type", tc.get("status", "unknown")),
            "traffic_confidence": tc.get("confidence", "N/A"),
            "risk_level": sec.get("risk_level", "UNKNOWN"),
            "finding_count": sec.get("findings_count", 0)
        }
        rows.append(row)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Saved batch summary CSV to {csv_path}")
