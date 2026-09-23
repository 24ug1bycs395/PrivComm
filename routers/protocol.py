import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from models.protocol_analysis import ProtocolAnalysisResult
from services.protocol_engine import ProtocolIdentificationEngine

router = APIRouter(prefix="/analyze", tags=["Protocol Identification"])
engine = ProtocolIdentificationEngine()


@router.post(
    "/protocol",
    response_model=ProtocolAnalysisResult,
    summary="Analyze PCAP for IPsec Protocol Characteristics",
    description="Accepts a PCAP or PCAPNG packet capture file and extracts deterministic IPsec VPN characteristics.",
    status_code=status.HTTP_200_OK,
)
async def analyze_protocol(
    pcap_file: UploadFile = File(..., description="PCAP or PCAPNG capture file to analyze")
) -> ProtocolAnalysisResult:
    """
    POST /analyze/protocol
    Dissects the uploaded PCAP file using the Protocol Identification Engine.
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

    # Save uploaded file to a temporary location safely
    suffix = os.path.splitext(pcap_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = temp_file.name
        try:
            shutil.copyfileobj(pcap_file.file, temp_file)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read and store upload: {str(e)}"
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
        # Guarantee cleanup of temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
