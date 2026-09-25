import os
import json
import csv
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

from security.explainability import generate_plain_english_explanations
from security.drift_detector import detect_configuration_drift
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

    report = {
        "capture": {
            "filename": ingest_res.get("filename", "unknown"),
            "filepath": ingest_res.get("filepath", "unknown"),
            "packet_count": ingest_res.get("packet_count", 0)
        },
        "ipsec": ipsec_info,
        "traffic_classification": traffic_res,
        "metadata_exposure": meta_exposure,
        "security_assessment": {
            "risk_score": risk_res.get("score", 0),
            "risk_level": risk_res.get("level", "SECURE"),
            "methodology": risk_res.get("method"),
            "findings_count": len(findings),
            "findings": [f.to_dict() if hasattr(f, "to_dict") else f for f in findings],
            "recommendations": recommendations,
            "metadata_exposure": meta_exposure
        },
        "explainability": explanations,
        "drift_detection": drift_res,
        "policy_as_code": policy_rules_res,
        "post_quantum_readiness": pqc_res
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
