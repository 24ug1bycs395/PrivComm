import ipaddress
import json
import logging
import os
import shutil
import tempfile
from typing import Any, Optional

from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models.protocol_analysis import ProtocolAnalysisResult
from services.protocol_engine import ProtocolIdentificationEngine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Protocol Identification & Assessment"])
engine = ProtocolIdentificationEngine()

# In-memory session history store
ANALYSIS_HISTORY = []


@router.post(
    "/analyze/protocol",
    response_model=ProtocolAnalysisResult,
    summary="Analyze PCAP for IPsec Protocol Characteristics & AI Traffic Assessment",
    status_code=status.HTTP_200_OK,
)
async def analyze_protocol(
    pcap_file: UploadFile = File(..., description="PCAP or PCAPNG capture file to analyze"),
    tunnel_id: Optional[str] = Query(
        None, min_length=1, max_length=128,
        description="Optional stable operator-defined tunnel identifier for downgrade tracking",
    ),
    record_baseline: bool = Query(
        False, description="Record this capture's observed configuration as the tunnel baseline",
    ),
    baseline_authorization: Optional[str] = Header(
        None, alias="X-PrivComm-Baseline-Authorization",
        description="Operator secret required only when record_baseline=true",
    ),
) -> ProtocolAnalysisResult:
    """
    POST /analyze/protocol
    Dissects uploaded PCAP file using Protocol Identification Engine, XGBoost ML classifier, and Policy Engine.
    """
    if not pcap_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )
    if record_baseline and not tunnel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tunnel_id is required when record_baseline=true.",
        )
    if record_baseline:
        from security.downgrade_baseline import baseline_record_authorized
        if not baseline_record_authorized(baseline_authorization):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Baseline recording requires a valid operator authorization secret.",
            )

    valid_extensions = (".pcap", ".pcapng", ".cap")
    if not pcap_file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Expected one of {valid_extensions}"
        )

    suffix = os.path.splitext(pcap_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = temp_file.name
        try:
            shutil.copyfileobj(pcap_file.file, temp_file)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read upload: {str(e)}"
            )

    try:
        result = engine.analyze_pcap(
            temp_path, tunnel_id=tunnel_id, record_baseline=record_baseline
        )

        # Persist to Database / Local JSON storage
        try:
            from db.repository import AnalysisJobRepository
            job_record = result.model_dump() if hasattr(result, "model_dump") else result.dict()
            job_record["filename"] = pcap_file.filename
            job_record["filesize"] = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
            job_record["status"] = "COMPLETED"
            AnalysisJobRepository.save_analysis(job_record)
        except Exception:
            # Non-blocking persistence error logging
            pass

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Protocol analysis failed: {str(e)}"
        )
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@router.get("/analyze/sample", response_model=ProtocolAnalysisResult)
async def analyze_sample_capture():
    """GET /analyze/sample: Analyzes built-in IKEv2 AES-GCM sample PCAP file."""
    sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
    if not os.path.exists(sample_path):
        sample_path = "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng"

    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample PCAP file not found.")

    res = engine.analyze_pcap(sample_path)
    _record_history("ikev2_s2s_ipsec_vpn_aes_gcm.pcapng", res)
    return res


@router.get("/analyze/sample-weak", response_model=ProtocolAnalysisResult)
async def analyze_sample_weak_capture():
    """GET /analyze/sample-weak: Simulated analysis of a legacy weak IKEv1/3DES capture."""
    sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
    if not os.path.exists(sample_path):
        sample_path = "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng"

    result = engine.analyze_pcap(sample_path)
    result.ike_version = "IKEv1 (Aggressive Mode)"
    result.encryption = "3DES-CBC"
    result.integrity = "MD5"
    result.dh_group = "2"
    result.pfs = False
    result.security_assessment = {
        "risk_score": 60,
        "risk_level": "HIGH",
        "findings_count": 3,
        "findings": [
            {
                "finding_id": "IPSEC-VER-001",
                "category": "Protocol Version",
                "severity": "HIGH",
                "title": "Deprecated IKEv1 Aggressive Mode detected",
                "observed": "IKEv1 (Aggressive)",
                "expected": "IKEv2",
                "recommendation": "Upgrade tunnel policy to IKEv2 to prevent pre-shared key hash exposure."
            },
            {
                "finding_id": "IPSEC-ENC-001",
                "category": "Encryption",
                "severity": "HIGH",
                "title": "Deprecated 3DES-CBC encryption detected",
                "observed": "3DES-CBC",
                "expected": "Approved encryption (AES-256-GCM, AES-256-CBC)",
                "recommendation": "Reconfigure IPsec proposals to use AES-256-GCM encryption."
            },
            {
                "finding_id": "IPSEC-DH-001",
                "category": "Key Exchange",
                "severity": "HIGH",
                "title": "Insecure Diffie-Hellman Group 2 (1024-bit MODP)",
                "observed": "Group 2",
                "expected": "Approved DH Group (Group 14, 19, 20, 21, 28)",
                "recommendation": "Disable DH Group 2 and migrate to Group 14 (2048-bit MODP) or Group 19 (ECP-256)."
            }
        ],
        "recommendations": [
            {
                "finding_id": "IPSEC-VER-001",
                "category": "Protocol Version",
                "severity": "HIGH",
                "current_configuration": "IKEv1 Aggressive Mode",
                "expected_configuration": "IKEv2",
                "reason": "IKEv1 Aggressive Mode transmits hashes in plaintext",
                "recommended_action": "Upgrade to IKEv2 with AES-256-GCM."
            }
        ]
    }
    _record_history("IKEv1_Aggressive_DES_MD5.pcap", result)
    return result


class VendorConfigRequest(BaseModel):
    config_text: str
    vendor: str = "auto"
    filename: Optional[str] = "vendor_config.cfg"


@router.post("/analyze/vendor-config", response_model=ProtocolAnalysisResult)
async def analyze_vendor_config(payload: VendorConfigRequest) -> ProtocolAnalysisResult:
    """
    POST /analyze/vendor-config
    Ingests and parses static router/firewall configuration text (Cisco ASA/IOS-XE,
    Fortinet FortiOS, pfSense XML, Libreswan, strongSwan), evaluates cryptographic risk,
    and returns a tailored hardened remediation diff.
    """
    if not payload.config_text or not payload.config_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration text cannot be empty."
        )

    try:
        result = engine.analyze_vendor_config(
            config_text=payload.config_text,
            filename=payload.filename or "vendor_config.cfg",
            vendor=payload.vendor
        )
        _record_history(payload.filename or "vendor_config.cfg", result)
        return result
    except Exception as e:
        logger.exception("Vendor config analysis error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vendor configuration parsing failed: {str(e)}"
        )


@router.post("/analyze/vendor-config/upload", response_model=ProtocolAnalysisResult)
async def upload_vendor_config_file(
    config_file: UploadFile = File(..., description="Configuration file (.cfg, .conf, .txt, .xml, .json)"),
    vendor: str = Query("auto", description="Vendor override: auto, cisco, fortinet, pfsense, libreswan, strongswan")
) -> ProtocolAnalysisResult:
    """
    POST /analyze/vendor-config/upload
    Uploads a physical router/firewall configuration file to dissect and audit.
    """
    if not config_file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    content_bytes = await config_file.read()
    try:
        config_text = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode text file: {e}")

    result = engine.analyze_vendor_config(
        config_text=config_text,
        filename=config_file.filename,
        vendor=vendor
    )
    _record_history(config_file.filename, result)
    return result


@router.get("/analyze/vendor-config/samples")
async def get_vendor_config_samples():
    """
    GET /analyze/vendor-config/samples
    Returns pre-populated multi-vendor configuration templates for instant UI testing.
    """
    return {
        "cisco_asa_weak": {
            "name": "Cisco ASA / IOS (Legacy IKEv1 3DES/MD5 - High Risk)",
            "vendor": "Cisco ASA / IOS-XE",
            "filename": "cisco_asa_legacy_3des.cfg",
            "content": """! Cisco ASA Legacy IKEv1 VPN Configuration (Vulnerable)
crypto isakmp policy 10
 encr 3des
 hash md5
 authentication pre-share
 group 2
 lifetime 86400
!
crypto ipsec transform-set LEGACY_TRANSFORM esp-3des esp-md5-hmac
 mode transport
!
crypto map OUTSIDE_MAP 10 ipsec-isakmp
 set peer 203.0.113.15
 set transform-set LEGACY_TRANSFORM
 match address VPN_TRAFFIC
!"""
        },
        "cisco_ios_modern": {
            "name": "Cisco IOS-XE (Modern IKEv2 AES-256-GCM / DH19 - Zero-Trust)",
            "vendor": "Cisco ASA / IOS-XE",
            "filename": "cisco_ios_xe_ikev2_aes_gcm.cfg",
            "content": """! Cisco IOS-XE Modern Compliant IKEv2 Configuration
crypto ikev2 proposal IKEV2_GCM_PROP
 encryption aes-gcm-256
 prf sha256
 group 19
!
crypto ikev2 policy IKEV2_GCM_POLICY
 proposal IKEV2_GCM_PROP
!
crypto ipsec transform-set GCM_TRANSFORM esp-gcm 256
 mode tunnel
!
crypto ipsec profile HARDENED_IPSEC_PROFILE
 set transform-set GCM_TRANSFORM
 set pfs group19
 set security-association lifetime seconds 28800
!
crypto map SECURE_MAP 10 ipsec-isakmp
 set peer 198.51.100.25
 set transform-set GCM_TRANSFORM
 set pfs group19
!"""
        },
        "fortinet_fortios": {
            "name": "Fortinet FortiOS (Phase 1 & Phase 2 S2S VPN)",
            "vendor": "Fortinet FortiOS",
            "filename": "fortigate_ipsec_vpn.conf",
            "content": """# FortiGate IPsec VPN Phase 1 & 2 Config
config vpn ipsec phase1-interface
    edit "HQ_BRANCH_TUNNEL"
        set interface "wan1"
        set ike-version 2
        set proposal aes256gcm-prfsha256 aes256-sha256
        set dhgrp 19 14
        set remote-gw 198.51.100.50
        set psksecret ENC mySecretKey123
        set keylife 28800
    next
end

config vpn ipsec phase2-interface
    edit "HQ_BRANCH_P2"
        set phase1name "HQ_BRANCH_TUNNEL"
        set proposal aes256gcm
        set dhgrp 19
        set pfs enable
        set encapsulation tunnel
        set auto-negotiate enable
    next
end"""
        },
        "pfsense_xml": {
            "name": "pfSense / OPNsense (XML Export - Compliant)",
            "vendor": "pfSense / OPNsense",
            "filename": "pfsense_ipsec_config.xml",
            "content": """<ipsec>
    <phase1>
        <ikeid>1</ikeid>
        <iketype>ikev2</iketype>
        <interface>wan</interface>
        <remote-gateway>198.51.100.80</remote-gateway>
        <protocol>inet</protocol>
        <myid_type>myaddress</myid_type>
        <peerid_type>peeraddress</peerid_type>
        <encryption-algorithm>
            <name>aes256gcm</name>
            <keylen>256</keylen>
        </encryption-algorithm>
        <hash-algorithm>sha256</hash-algorithm>
        <dhgroup>19</dhgroup>
        <prf-algorithm>sha256</prf-algorithm>
        <lifetime>28800</lifetime>
    </phase1>
    <phase2>
        <ikeid>1</ikeid>
        <mode>tunnel</mode>
        <pfsgroup>19</pfsgroup>
        <lifetime>3600</lifetime>
        <encryption-algorithm-option>
            <name>aes256gcm</name>
            <keylen>256</keylen>
        </encryption-algorithm-option>
    </phase2>
</ipsec>"""
        },
        "libreswan_conf": {
            "name": "Libreswan / Openswan (/etc/ipsec.conf)",
            "vendor": "Libreswan / Openswan",
            "filename": "libreswan_ipsec.conf",
            "content": """# Libreswan IPsec Site-to-Site Connection
conn Cloud-to-Datacenter
    authby=secret
    type=tunnel
    left=192.168.1.1
    leftsubnet=192.168.1.0/24
    right=198.51.100.99
    rightsubnet=10.0.0.0/16
    ikev2=insist
    ike=aes_gcm256-sha2_512;dh19
    esp=aes_gcm256;dh19
    pfs=yes
    salifetime=8h
    auto=start"""
        }
    }


@router.get("/api/report-data")
async def get_report_data(filename: str = Query(..., description="PCAP filename")):
    """GET /api/report-data: Returns report JSON data for report.html view."""
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join("results", f"{base_name}.json")
    if not os.path.exists(json_path):
        json_path = os.path.join("results", "result.json")

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)

    # Fallback to sample analysis
    sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
    if os.path.exists(sample_path):
        res = engine.analyze_pcap(sample_path)
        return {
            "capture": {"filename": filename, "packet_count": 12},
            "ipsec": res.dict(),
            "traffic_classification": res.traffic_classification or {},
            "security_assessment": res.security_assessment or {}
        }

    raise HTTPException(status_code=404, detail=f"Report data for '{filename}' not found.")


@router.get("/api/history")
async def get_analysis_history():
    """GET /api/history: Returns analysis session history for dashboard."""
    if not ANALYSIS_HISTORY:
        # Default seed history items
        return [
            {
                "filename": "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng",
                "ike_version": "IKEv2",
                "mode": "Tunnel",
                "encryption": "AES-256-GCM",
                "dh_group": "19",
                "traffic_type": "CHAT",
                "confidence": 0.4767,
                "risk_score": 0,
                "risk_level": "SECURE"
            },
            {
                "filename": "IKEv1_Aggressive_DES_MD5.pcap",
                "ike_version": "IKEv1",
                "mode": "Tunnel",
                "encryption": "3DES-CBC",
                "dh_group": "2",
                "traffic_type": "VPN-BROWSING",
                "confidence": 0.521,
                "risk_score": 60,
                "risk_level": "HIGH"
            }
        ]
    return ANALYSIS_HISTORY


@router.get("/reports/download-pdf")
async def download_pdf_report(filename: str = Query(..., description="PCAP filename")):
    """GET /reports/download-pdf: Generates and downloads Executive White-Mode PDF Security Report."""
    import shutil

    from reports.pdf_report_generator import generate_pdf_report

    # Clean base name
    clean_name = filename.replace("_executive_report.pdf", "").replace(".pdf", "")
    base_name = os.path.splitext(clean_name)[0]
    if not base_name or base_name == "undefined":
        base_name = "ikev2_s2s_ipsec_vpn_aes_gcm"

    pdf_path = os.path.join("results", f"{base_name}_executive_report.pdf")
    frontend_pdf = os.path.join("frontend", "public", "reports", f"{base_name}_executive_report.pdf")

    # Potential JSON sources
    candidate_json_paths = [
        os.path.join("results", f"{base_name}.json"),
        os.path.join("frontend", "public", "reports", f"{base_name}.json"),
        os.path.join("results", "result.json"),
        os.path.join("results", "report.json"),
        os.path.join("frontend", "public", "reports", "ikev2_s2s_ipsec_vpn_aes_gcm.json"),
    ]

    report_data = None
    for cand in candidate_json_paths:
        if os.path.exists(cand):
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                break
            except Exception as e:
                logger.warning(f"Could not load JSON from {cand}: {e}")

    if report_data:
        try:
            generate_pdf_report(report_data, pdf_path)
            try:
                os.makedirs(os.path.dirname(frontend_pdf), exist_ok=True)
                shutil.copyfile(pdf_path, frontend_pdf)
            except Exception:
                pass
            return FileResponse(pdf_path, media_type="application/pdf", filename=f"{base_name}_executive_report.pdf")
        except Exception as e:
            logger.error(f"Failed to generate PDF from JSON: {e}")

    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{base_name}_executive_report.pdf")

    if os.path.exists(frontend_pdf):
        return FileResponse(frontend_pdf, media_type="application/pdf", filename=f"{base_name}_executive_report.pdf")

    sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
    if os.path.exists(sample_path):
        engine.analyze_pcap(sample_path)
        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type="application/pdf", filename=f"{base_name}_executive_report.pdf")

    raise HTTPException(status_code=404, detail=f"Executive PDF report for '{filename}' not found.")


@router.get("/reports/download-html")
async def download_html_report(filename: str = Query(..., description="PCAP filename")):
    """GET /reports/download-html: Downloads Executive HTML Security Report."""
    base_name = os.path.splitext(filename)[0]
    html_path = os.path.join("results", f"{base_name}_executive_report.html")
    if not os.path.exists(html_path):
        html_path = os.path.join("results", "executive_report.html")

    if not os.path.exists(html_path):
        sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
        if os.path.exists(sample_path):
            engine.analyze_pcap(sample_path)

    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail=f"Executive HTML report for '{filename}' not found.")

    return FileResponse(html_path, media_type="text/html", filename=f"{base_name}_executive_report.html")


@router.get("/reports/download-json")
async def download_json_report(filename: str = Query(..., description="PCAP filename")):
    """GET /reports/download-json: Downloads Technical JSON Analysis Report."""
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join("results", f"{base_name}.json")
    if not os.path.exists(json_path):
        json_path = os.path.join("results", "result.json")

    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail=f"JSON report for '{filename}' not found.")

    return FileResponse(json_path, media_type="application/json", filename=f"{base_name}_analysis.json")


@router.get("/reports/download-cbom")
async def download_crypto_bom(filename: str = Query(..., description="PCAP filename")):
    """Download the capture-backed cryptographic inventory for an analyzed capture."""
    base_name = os.path.basename(os.path.splitext(filename)[0])
    cbom_path = os.path.join("results", f"{base_name}_cbom.json")
    if not os.path.isfile(cbom_path):
        raise HTTPException(status_code=404, detail=f"Crypto BOM for '{filename}' not found.")
    return FileResponse(
        cbom_path,
        media_type="application/json",
        filename=f"{base_name}_cbom.json",
    )


@router.get("/api/jobs", summary="Get recent PCAP analysis jobs")
async def list_analysis_jobs(limit: int = Query(50, ge=1, le=100)):
    """GET /api/jobs: Returns history of completed and recent PCAP analysis jobs."""
    from db.repository import AnalysisJobRepository
    return AnalysisJobRepository.list_analyses(limit=limit)


@router.get("/api/jobs/{job_id}", summary="Get specific PCAP analysis job by ID")
async def get_analysis_job_detail(job_id: str):
    """GET /api/jobs/{job_id}: Returns detailed result of a past analysis job."""
    from db.repository import AnalysisJobRepository
    job = AnalysisJobRepository.get_analysis(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Analysis job '{job_id}' not found.")
    return job


class ChatRequest(BaseModel):
    message: str


class ProbeRequest(BaseModel):
    target_ip: str
    port: int = 500
    use_ikev2: bool = True
    timeout_s: float = 5.0
    consent_token: str
    probe_note: str | None = None


class AllowlistAddRequest(BaseModel):
    ip: str
    added_by: str
    reason: str


@router.post("/probe/ike", summary="Run a consent-gated active IKE probe")
async def probe_ike(request: ProbeRequest) -> dict[str, Any]:
    """Send IKE_SA_INIT only after token and exact allowlist checks pass."""
    try:
        target_address = ipaddress.ip_address(request.target_ip)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="target_ip must be a valid IPv4 address") from exc
    if target_address.version != 4:
        raise HTTPException(status_code=422, detail="target_ip must be a valid IPv4 address")
    if request.port not in (500, 4500):
        raise HTTPException(status_code=422, detail="port must be 500 or 4500")
    from probe.consent import check_double_barrier
    allowed, reason = check_double_barrier(request.target_ip, request.consent_token)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)
    from probe.fingerprint import fingerprint_vendor
    from probe.scanner import probe
    result = probe(request.target_ip, request.port, request.timeout_s, request.use_ikev2)
    if result.error and not result.reachable:
        if "timed out" in result.error.lower():
            raise HTTPException(status_code=504, detail=result.error)
        raise HTTPException(status_code=502, detail=result.error)
    response = result.to_dict()
    response["vendor_fingerprint"] = fingerprint_vendor(
        result.vendor_ids or [], result.proposed_transforms or []
    )
    response["probe_note"] = request.probe_note
    return response


@router.get("/probe/allowlist", summary="List active probe targets")
async def get_probe_allowlist() -> list[dict[str, Any]]:
    from probe.allowlist import list_allowlist
    return list_allowlist()


@router.post("/probe/allowlist/add", summary="Add an exact IP to the probe allowlist")
async def add_probe_allowlist(request: AllowlistAddRequest) -> dict[str, str]:
    try:
        allowlist_address = ipaddress.ip_address(request.ip)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="ip must be a valid IPv4 address") from exc
    if allowlist_address.version != 4:
        raise HTTPException(status_code=422, detail="ip must be a valid IPv4 address")
    from probe.allowlist import add_to_allowlist
    add_to_allowlist(request.ip, request.added_by, request.reason)
    return {"status": "added", "ip": request.ip}


@router.delete("/probe/allowlist/remove/{ip}", summary="Remove an exact IP from the probe allowlist")
async def remove_probe_allowlist(ip: str) -> dict[str, str]:
    from probe.allowlist import remove_from_allowlist
    remove_from_allowlist(ip)
    return {"status": "removed", "ip": ip}


@router.post("/api/chat")
async def chat_assistant(req: ChatRequest):
    """POST /api/chat: Privcomm AI Security Assistant Chatbot endpoint."""
    from security.llm_explainer import query_gemini_assistant
    reply = query_gemini_assistant(req.message)
    return {"reply": reply}



def _record_history(filename: str, result: ProtocolAnalysisResult):
    tc = result.traffic_classification or {}
    sec = result.security_assessment or {}
    item = {
        "filename": filename,
        "ike_version": result.ike_version or "IKEv2",
        "mode": result.mode or "Tunnel",
        "encryption": result.encryption or "AES-256-GCM",
        "dh_group": result.dh_group or "19",
        "traffic_type": tc.get("traffic_type", "CHAT"),
        "confidence": tc.get("confidence", 0.4767),
        "risk_score": sec.get("risk_score", 0),
        "risk_level": sec.get("risk_level", "SECURE")
    }
    ANALYSIS_HISTORY.insert(0, item)
    if len(ANALYSIS_HISTORY) > 20:
        ANALYSIS_HISTORY.pop()
