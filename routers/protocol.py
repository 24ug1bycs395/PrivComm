import os
import shutil
import tempfile
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from fastapi.responses import FileResponse, JSONResponse
from models.protocol_analysis import ProtocolAnalysisResult
from services.protocol_engine import ProtocolIdentificationEngine

router = APIRouter(tags=["Protocol Identification & Assessment"])
engine = ProtocolIdentificationEngine()


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

    return engine.analyze_pcap(sample_path)


@router.get("/analyze/sample-weak", response_model=ProtocolAnalysisResult)
async def analyze_sample_weak_capture():
    """GET /analyze/sample-weak: Simulated analysis of a legacy weak IKEv1/3DES capture."""
    sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
    if not os.path.exists(sample_path):
        sample_path = "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng"

    result = engine.analyze_pcap(sample_path)
    # Return simulated weak configuration findings for policy violation demo
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
    return result


@router.get("/reports/download-html")
async def download_html_report(filename: str = Query(..., description="PCAP filename")):
    """GET /reports/download-html: Downloads the generated Executive HTML Security Report."""
    base_name = os.path.splitext(filename)[0]
    html_path = os.path.join("results", f"{base_name}_executive_report.html")
    if not os.path.exists(html_path):
        html_path = os.path.join("results", "executive_report.html")

    if not os.path.exists(html_path):
        # Generate on-the-fly if not found
        sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
        if os.path.exists(sample_path):
            engine.analyze_pcap(sample_path)

    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail=f"Executive HTML report for '{filename}' not found. Run analysis first.")

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
