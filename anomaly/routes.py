"""FastAPI endpoints for VPN Behavioral Anomaly Detection."""

from __future__ import annotations
import os
import shutil
import tempfile
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status

from anomaly.schemas import (
    AnomalyModelStatus,
    AnomalyBaselineMetric,
    AnomalyPredictRequest,
    AnomalyPredictionResult,
    AnomalyPcapAnalysisResponse,
)
from anomaly import service

router = APIRouter(prefix="/anomaly", tags=["VPN Behavioral Anomaly Detection"])


@router.get(
    "/status",
    response_model=AnomalyModelStatus,
    summary="Get Anomaly Detection Model Status & Metadata",
)
async def get_anomaly_status():
    """Returns the current anomaly detection model configuration, features, and threshold."""
    return service.get_status()


@router.get(
    "/baseline",
    response_model=List[AnomalyBaselineMetric],
    summary="Get Learned Normal Baseline Metrics for Features",
)
async def get_anomaly_baseline():
    """Returns baseline median and IQR stats across all 32 observable behavioral features."""
    return service.get_baseline()


@router.post(
    "/detect",
    response_model=AnomalyPredictionResult,
    summary="Evaluate Behavioral Features for Anomaly",
)
async def detect_anomaly_features(payload: AnomalyPredictRequest):
    """
    Score a raw or aggregate set of 32 behavioral features against the learned normal baseline.
    Returns calibrated anomaly score (0-1), prediction ('normal'/'anomalous'), and top contributing deviations.
    """
    try:
        return service.predict_sample(payload.features, top_k=payload.top_k)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.post(
    "/detect-pcap",
    response_model=AnomalyPcapAnalysisResponse,
    summary="Analyze PCAP File for Behavioral Anomalies across Time Windows",
)
async def detect_anomaly_pcap(
    pcap_file: UploadFile = File(..., description="PCAP/PCAPNG capture file to analyze"),
    window_sec: float = Query(60.0, ge=5.0, le=600.0, description="Window size in seconds"),
    step_sec: float = Query(30.0, ge=1.0, le=300.0, description="Sliding window step size in seconds"),
):
    """
    Dissects uploaded PCAP file into time windows, extracts 32 observable behavioral features,
    and runs anomaly inference to identify behavioral deviations (traffic spikes, flow anomalies, etc.).
    """
    if not pcap_file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    valid_exts = (".pcap", ".pcapng", ".cap")
    if not pcap_file.filename.lower().endswith(valid_exts):
        raise HTTPException(status_code=400, detail=f"File extension must be one of {valid_exts}")

    suffix = os.path.splitext(pcap_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        try:
            shutil.copyfileobj(pcap_file.file, tmp)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    try:
        res = service.analyze_pcap_windows(tmp_path, window_sec=window_sec, step_sec=step_sec)
        res.filename = pcap_file.filename
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PCAP anomaly analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
