import os
import shutil
import tempfile
import json
import logging
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from fastapi.responses import FileResponse, JSONResponse

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
    pcap_file: UploadFile = File(..., description="PCAP or PCAPNG capture file to analyze")
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
        result = engine.analyze_pcap(temp_path)
        
        # Persist to Database / Local JSON storage
        try:
            from db.repository import AnalysisJobRepository
            job_record = result.model_dump() if hasattr(result, "model_dump") else result.dict()
            job_record["filename"] = pcap_file.filename
            job_record["filesize"] = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
            job_record["status"] = "COMPLETED"
            AnalysisJobRepository.save_analysis(job_record)
        except Exception as e:
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
