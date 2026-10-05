import logging
import os
from typing import Optional

from analyzer.pcap_ingestion import ingest_and_parse_pcap
from analyzer.provenance import build_data_provenance
from ml.xgboost_adapter import predict_traffic_class
from models.protocol_analysis import ProtocolAnalysisResult
from reports.html_report_generator import generate_html_report
from reports.report_generator import build_unified_analysis_report
from security.policy_engine import evaluate_ipsec_security
from security.recommendations import generate_recommendations
from security.risk import calculate_security_risk

logger = logging.getLogger("ProtocolIdentificationEngine")


class ProtocolIdentificationEngine:
    """
    Unified Protocol & AI Security Intelligence Engine.
    Combines PCAP protocol dissection, XGBoost traffic classification,
    and context-aware security policy auditing.
    """

    def analyze_pcap(
        self,
        pcap_path: str,
        tunnel_id: Optional[str] = None,
        record_baseline: bool = False,
    ) -> ProtocolAnalysisResult:
        """
        Analyze the given PCAP file and return complete analysis result.
        """
        if not os.path.exists(pcap_path):
            raise FileNotFoundError(f"PCAP file not found: {pcap_path}")

        # 1. Ingest PCAP & parse protocols
        ingest_res = ingest_and_parse_pcap(pcap_path)
        ipsec = ingest_res.get("ipsec", {})

        rfc4303_result = None
        esp_packets = ingest_res.get("zdp_esp_packets", [])
        if esp_packets:
            from analyzer.rfc4303 import eliminate_impossible_ciphers
            rfc4303_result = eliminate_impossible_ciphers(esp_packets).to_dict()
            viable = rfc4303_result.get("viable_ciphers", [])
            if len(viable) == 1:
                ipsec["encryption"] = viable[0]
                ipsec["encryption_provenance"] = "rfc4303_arithmetic"

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
                from anomaly import service as anomaly_service
                from anomaly.feature_adapter import adapt_flow_features_to_behavioral
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
        cbom_output = os.path.join("results", f"{base_filename}_cbom.json")

        report_data = build_unified_analysis_report(ingest_res, traffic_res, findings, recommendations, risk_res)
        downgrade_tracking = None
        if record_baseline and not tunnel_id:
            raise ValueError("tunnel_id is required when recording a tunnel baseline.")
        if tunnel_id:
            from security.downgrade_baseline import (
                compare_tunnel_baseline,
                record_tunnel_baseline,
            )
            if record_baseline:
                entry = record_tunnel_baseline(
                    tunnel_id, ipsec, ingest_res.get("capture_sha256", "")
                )
                downgrade_tracking = {
                    "tunnel_id": entry["tunnel_id"],
                    "status": "BASELINE_RECORDED",
                    "recorded_at": entry["recorded_at"],
                    "capture_sha256": entry["capture_sha256"],
                }
            else:
                downgrade_tracking = compare_tunnel_baseline(tunnel_id, ipsec)
            report_data["downgrade_tracking"] = downgrade_tracking
        data_provenance = build_data_provenance(
            ingest_result=ingest_res,
            ipsec=ipsec,
            traffic_classification=traffic_res,
            behavioral_anomaly=anomaly_res,
            metadata_exposure=meta_exposure,
            rfc4303_elimination=rfc4303_result,
        )
        report_data["data_provenance"] = data_provenance
        generate_html_report(report_data, html_output)

        from reports.report_generator import save_json_report
        save_json_report(report_data, json_output)
        save_json_report(report_data["crypto_bom"], cbom_output)
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
        StorageService.upload_report_html(f"{base_filename}_executive_report.html", html_output)

        # Format dh_group representation
        dh_val = ipsec.get("dh_group")
        dh_str = str(dh_val) if dh_val not in (None, "unknown") else None

        pfs_val = ipsec.get("pfs")
        if pfs_val == "unknown":
            pfs_val = None
        replay_protection_val = ipsec.get("replay_protection")
        if replay_protection_val == "unknown":
            replay_protection_val = None

        # Mode and confidence
        mode_val = ipsec.get("mode") if ipsec.get("mode") != "unknown" else None

        # IP version & endpoint IPs (dynamically extracted from wire headers, not hardcoded)
        return ProtocolAnalysisResult(
            ipsec_detected=ipsec.get("detected", False),
            ike_version=ipsec.get("ike_version") if ipsec.get("ike_version") != "unknown" else None,
            esp_detected=ipsec.get("esp_detected", False),
            ah_detected=ipsec.get("ah_detected", False),
            mode=mode_val,
            mode_confidence=ipsec.get("mode_confidence"),
            encryption=ipsec.get("encryption") if ipsec.get("encryption") != "unknown" else None,
            integrity=ipsec.get("integrity") if ipsec.get("integrity") != "unknown" else None,
            dh_group=dh_str,
            pfs=pfs_val,
            replay_protection=replay_protection_val,
            ip_version=ingest_res.get("ip_version"),
            source_ip=ingest_res.get("source_ip"),
            destination_ip=ingest_res.get("destination_ip"),
            traffic_classification=traffic_res,
            behavioral_anomaly=anomaly_res,
            metadata_exposure=meta_exposure,
            security_assessment=report_data.get("security_assessment"),
            explainability=report_data.get("explainability", []),
            rfc4303_elimination=rfc4303_result,
            data_provenance=data_provenance,
            capture_sha256=ingest_res.get("capture_sha256"),
            packet_evidence=ingest_res.get("packet_evidence", []),
            downgrade_tracking=downgrade_tracking,
            crypto_bom=report_data.get("crypto_bom"),
            analysis_source="pcap",
            report_html=os.path.abspath(html_output)
        )

    def analyze_vendor_config(self, config_text: str, filename: str = "config.cfg", vendor: str = "auto") -> ProtocolAnalysisResult:
        """
        Parses static router/firewall configuration text (Cisco, Fortinet, pfSense, Libreswan, strongSwan),
        runs security policy evaluations, drift checks, post-quantum assessment, and produces
        a hardened vendor remediation snippet.
        """
        from analyzer.vendor_config_parser import VendorConfigParser
        parsed = VendorConfigParser.parse_config(config_text, override_vendor=vendor)

        ipsec = {
            "detected": True,
            "ike_detected": True,
            "ike_version": parsed.get("ike_version") or "unknown",
            "esp_detected": False,
            "ah_detected": False,
            "encryption": parsed.get("encryption") or "unknown",
            "integrity": parsed.get("integrity") or "unknown",
            "dh_group": str(parsed["dh_group"]) if parsed.get("dh_group") is not None else "unknown",
            "pfs": parsed.get("pfs"),
            "mode": parsed.get("mode"),
            "prf": parsed.get("prf"),
            "key_length": parsed.get("key_length"),
            "source_ip": parsed.get("source_ip"),
            "destination_ip": parsed.get("destination_ip"),
        }

        traffic_res = None

        findings = evaluate_ipsec_security(ipsec)
        recommendations = generate_recommendations(findings)
        risk_res = calculate_security_risk(findings)

        meta_exposure = None

        ingest_res = {
            "packet_count": 0,
            "ipsec": ipsec,
            "flow_features": None,
            "ip_version": None,
            "source_ip": ipsec["source_ip"],
            "destination_ip": ipsec["destination_ip"],
            "metadata_exposure": meta_exposure
        }

        report_data = build_unified_analysis_report(ingest_res, traffic_res, findings, recommendations, risk_res)
        data_provenance = {
            "analysis_source": "PARSED",
            "vendor": parsed.get("provenance", "UNKNOWN"),
            **parsed.get("field_provenance", {}),
            "risk_score": "INFERRED",
            "traffic_classification": "NOT_APPLICABLE",
        }
        report_data["data_provenance"] = data_provenance
        report_data["vendor"] = parsed.get("vendor")
        report_data["remediation_config"] = parsed.get("remediation_config")

        base_filename = os.path.splitext(os.path.basename(filename))[0] or "vendor_config"
        html_output = os.path.join("results", f"{base_filename}_executive_report.html")
        json_output = os.path.join("results", f"{base_filename}.json")

        os.makedirs("results", exist_ok=True)
        generate_html_report(report_data, html_output)
        from reports.report_generator import save_json_report
        save_json_report(report_data, json_output)

        dh_str = str(ipsec.get("dh_group"))
        mode_val = ipsec.get("mode", "Tunnel")

        return ProtocolAnalysisResult(
            ipsec_detected=True,
            ike_version=ipsec.get("ike_version"),
            esp_detected=None,
            ah_detected=None,
            mode=mode_val,
            mode_confidence=None,
            encryption=ipsec.get("encryption"),
            integrity=ipsec.get("integrity"),
            dh_group=dh_str,
            pfs=ipsec.get("pfs"),
            replay_protection=None,
            ip_version=None,
            source_ip=ipsec.get("source_ip"),
            destination_ip=ipsec.get("destination_ip"),
            traffic_classification=traffic_res,
            behavioral_anomaly=None,
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
            data_provenance=data_provenance,
            vendor=parsed.get("vendor"),
            remediation_config=parsed.get("remediation_config"),
            raw_config_lines=parsed.get("raw_config_lines"),
            analysis_source="vendor_config",
            report_html=os.path.abspath(html_output)
        )
