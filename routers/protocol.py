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
    """GET /analyze/sample: Analyzes built-in sample PCAP file."""
    sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
    if not os.path.exists(sample_path):
        sample_path = "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng"

    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample PCAP file not found.")

    return engine.analyze_pcap(sample_path)


@router.get("/reports/download-html")
async def download_html_report(filename: str = Query(..., description="PCAP filename")):
    """GET /reports/download-html: Downloads the generated Executive HTML Security Report."""
    base_name = os.path.splitext(filename)[0]
    html_path = os.path.join("results", f"{base_name}_executive_report.html")
    if not os.path.exists(html_path):
        html_path = os.path.join("results", "executive_report.html")

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
