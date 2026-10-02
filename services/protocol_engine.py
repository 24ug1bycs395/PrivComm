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

        # 2b. Evaluate VPN Behavioral Anomaly Detection
        anomaly_res = None
        try:
            from anomaly import service as anomaly_service
            pcap_anom = anomaly_service.analyze_pcap_windows(pcap_path)
            anomaly_res = pcap_anom.model_dump() if hasattr(pcap_anom, "model_dump") else pcap_anom.dict()
        except Exception as anom_err:
            logger.warning(f"VPN Behavioral Anomaly analysis encountered an issue: {anom_err}")
            try:
                from anomaly.feature_adapter import adapt_flow_features_to_behavioral
                from anomaly import service as anomaly_service
                adapted_feats = adapt_flow_features_to_behavioral(flow_feats)
                single_pred = anomaly_service.predict_sample(adapted_feats)
                dumped = single_pred.model_dump() if hasattr(single_pred, "model_dump") else single_pred.dict()
                anomaly_res = {
                    "status": "success",
                    "filename": pcap_path,
                    "total_windows": 1,
                    "anomalous_windows": 1 if dumped.get("prediction") == "anomalous" else 0,
                    "overall_anomaly_score": dumped.get("anomaly_score", 0.0),
                    "overall_prediction": dumped.get("prediction", "normal"),
                    "overall_severity": dumped.get("severity", "LOW"),
                    "window_results": [dumped],
                    "top_deviations": dumped.get("top_contributing_features", []),
                }
            except Exception:
                anomaly_res = None

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

        # 4. Generate Executive HTML, PDF & JSON Reports
        base_filename = os.path.splitext(os.path.basename(pcap_path))[0]
        html_output = os.path.join("results", f"{base_filename}_executive_report.html")
        pdf_output = os.path.join("results", f"{base_filename}_executive_report.pdf")
        json_output = os.path.join("results", f"{base_filename}.json")

        report_data = build_unified_analysis_report(ingest_res, traffic_res, findings, recommendations, risk_res)
        generate_html_report(report_data, html_output)

        from reports.report_generator import save_json_report
        save_json_report(report_data, json_output)
        save_json_report(report_data, os.path.join("results", "result.json"))

        try:
            from reports.pdf_report_generator import generate_pdf_report
            generate_pdf_report(report_data, pdf_output)
            
            # Sync to frontend/public/reports for instant static and web access
            import shutil
            frontend_dir = os.path.join("frontend", "public", "reports")
            os.makedirs(frontend_dir, exist_ok=True)
            shutil.copyfile(pdf_output, os.path.join(frontend_dir, f"{base_filename}_executive_report.pdf"))
            shutil.copyfile(pdf_output, os.path.join(frontend_dir, "executive_report.pdf"))
            shutil.copyfile(html_output, os.path.join(frontend_dir, f"{base_filename}_executive_report.html"))
            save_json_report(report_data, os.path.join(frontend_dir, f"{base_filename}.json"))
        except Exception as e:
            logger.warning(f"Could not generate or sync PDF report: {e}")

        from db.storage import StorageService
        report_url = StorageService.upload_report_html(f"{base_filename}_executive_report.html", html_output)

        # Format dh_group representation
        dh_val = ipsec.get("dh_group")
        dh_str = str(dh_val) if dh_val not in (None, "unknown") else None

        pfs_val = True if ipsec.get("pfs") in (True, "enforced", "yes") else False

        # Mode and confidence
        mode_val = ipsec.get("mode") if ipsec.get("mode") != "unknown" else None

        # IP version & endpoint IPs (dynamically extracted from wire headers, not hardcoded)
        ip_ver = ipsec.get("ip_version")
        if not ip_ver or ip_ver == "unknown":
            ip_ver = "IPv4"

        return ProtocolAnalysisResult(
            ipsec_detected=ipsec.get("detected", False),
            ike_version=ipsec.get("ike_version") if ipsec.get("ike_version") != "unknown" else None,
            esp_detected=ipsec.get("esp_detected", False),
            ah_detected=ipsec.get("ah_detected", False),
            mode=mode_val,
            mode_confidence="high" if mode_val == "Tunnel" else "medium",
            encryption=ipsec.get("encryption") if ipsec.get("encryption") != "unknown" else None,
            integrity=ipsec.get("integrity") if ipsec.get("integrity") != "unknown" else None,
            dh_group=dh_str,
            pfs=pfs_val,
            replay_protection=True if ipsec.get("esp_detected") or ipsec.get("ah_detected") else False,
            ip_version=ingest_res.get("ip_version", "IPv4"),
            source_ip=ingest_res.get("source_ip"),
            destination_ip=ingest_res.get("destination_ip"),
            traffic_classification=traffic_res,
            behavioral_anomaly=anomaly_res,
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
