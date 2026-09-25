import os
import shutil
import logging
from typing import Dict, Any, Optional

from models.protocol_analysis import ProtocolAnalysisResult
from analyzer.pcap_ingestion import ingest_and_parse_pcap
from ml.xgboost_adapter import predict_traffic_class
from security.policy_engine import evaluate_ipsec_security
from security.recommendations import generate_recommendations
from security.risk import calculate_security_risk
from reports.report_generator import build_unified_analysis_report
from reports.html_report_generator import generate_html_report

logger = logging.getLogger("ProtocolIdentificationEngine")


class ProtocolIdentificationEngine:
    """
    Unified Protocol & AI Security Intelligence Engine.
    Combines PCAP protocol dissection, XGBoost traffic classification,
    and context-aware security policy auditing.
    """

    def analyze_pcap(self, pcap_path: str) -> ProtocolAnalysisResult:
        """
        Analyze the given PCAP file and return complete analysis result.
        """
        if not os.path.exists(pcap_path):
            raise FileNotFoundError(f"PCAP file not found: {pcap_path}")

        # 1. Ingest PCAP & parse protocols
        ingest_res = ingest_and_parse_pcap(pcap_path)
        ipsec = ingest_res.get("ipsec", {})

        # 2. Predict Traffic Class using trained XGBoost ML model
        flow_feats = ingest_res.get("flow_features", {})
        traffic_res = predict_traffic_class(flow_feats)
        predicted_type = traffic_res.get("traffic_type") if traffic_res.get("status") == "success" else None

        # 3. Context-Aware Security Policy Audit & Observable Metadata Exposure
        findings = evaluate_ipsec_security(ipsec, traffic_type=predicted_type)

        meta_exposure = ingest_res.get("metadata_exposure", {})
        from security.findings import SecurityFinding
        for meta_f in meta_exposure.get("exposure_findings", []):
            findings.append(SecurityFinding(
                finding_id=meta_f.get("finding_id", "IPSEC-META-000"),
                category=meta_f.get("category", "Metadata Exposure"),
                severity=meta_f.get("severity", "MEDIUM"),
                title=meta_f.get("title", "Metadata Exposure Vulnerability"),
                observed=meta_f.get("observed", ""),
                expected=meta_f.get("expected", ""),
                recommendation=meta_f.get("recommendation", "")
            ))

        recommendations = generate_recommendations(findings)
        risk_res = calculate_security_risk(findings)

        # 4. Generate Executive HTML Report
        base_filename = os.path.splitext(os.path.basename(pcap_path))[0]
        html_output = os.path.join("results", f"{base_filename}_executive_report.html")
        report_data = build_unified_analysis_report(ingest_res, traffic_res, findings, recommendations, risk_res)
        generate_html_report(report_data, html_output)

        from db.storage import StorageService
        report_url = StorageService.upload_report_html(f"{base_filename}_executive_report.html", html_output)

        # Format dh_group representation
        dh_val = ipsec.get("dh_group")
        dh_str = str(dh_val) if dh_val not in (None, "unknown") else None

        pfs_val = True if ipsec.get("pfs") in (True, "enforced", "yes") else False

        return ProtocolAnalysisResult(
            ipsec_detected=ipsec.get("detected", False),
            ike_version=ipsec.get("ike_version") if ipsec.get("ike_version") != "unknown" else None,
            esp_detected=ipsec.get("esp_detected", False),
            ah_detected=ipsec.get("ah_detected", False),
            mode=ipsec.get("mode") if ipsec.get("mode") != "unknown" else None,
            encryption=ipsec.get("encryption") if ipsec.get("encryption") != "unknown" else None,
            integrity=ipsec.get("integrity") if ipsec.get("integrity") != "unknown" else None,
            dh_group=dh_str,
            pfs=pfs_val,
            replay_protection=True if ipsec.get("esp_detected") or ipsec.get("ah_detected") else False,
            ip_version=ingest_res.get("ip_version", "IPv4"),
            source_ip=ingest_res.get("source_ip"),
            destination_ip=ingest_res.get("destination_ip"),
            traffic_classification=traffic_res,
            metadata_exposure=meta_exposure,
            security_assessment={
                "risk_score": risk_res.get("score", 0),
                "risk_level": risk_res.get("level", "SECURE"),
                "findings_count": len(findings),
                "findings": [f.to_dict() if hasattr(f, "to_dict") else f for f in findings],
                "recommendations": recommendations,
                "metadata_exposure": meta_exposure
            },
            explainability=report_data.get("explainability", []),
            report_html=os.path.abspath(html_output)
        )

