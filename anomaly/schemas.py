"""Pydantic schemas for VPN Behavioral Anomaly Detection service."""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnomalyContributingFeature(BaseModel):
    feature: str = Field(..., description="Name of the behavioral feature")
    value: float = Field(..., description="Observed value for this feature in the window/sample")
    reason: str = Field(..., description="Plain-English explanation of deviation from learned normal baseline")
    baseline_median: float = Field(..., description="Learned median value for this feature in normal traffic")
    baseline_iqr: float = Field(..., description="Learned interquartile range (IQR) for this feature")


class AnomalyPredictionResult(BaseModel):
    prediction: str = Field(..., description="'normal' or 'anomalous'")
    anomaly_score: float = Field(..., description="Calibrated ranking score between 0.0 (baseline) and 1.0 (strongly anomalous)")
    severity: str = Field(default="LOW", description="'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'")
    detector: str = Field(..., description="Name of the underlying anomaly detector algorithm")
    score_definition: str = Field(default="Calibrated ranking score from 0 (normal-consistent) to 1 (strongly anomalous); not a probability.")
    top_contributing_features: List[AnomalyContributingFeature] = Field(default_factory=list, description="Top deviating features compared to baseline")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of observation window")
    window_duration_sec: Optional[float] = Field(default=None, description="Duration in seconds of the observation window")
    packet_count: Optional[int] = Field(default=None, description="Packet count in the observation window")
    byte_count: Optional[int] = Field(default=None, description="Byte count in the observation window")


class AnomalyPredictRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Key-value mapping of the 32 behavioral features")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top contributing features to return")


class AnomalyBaselineMetric(BaseModel):
    feature: str
    median: float
    iqr: float
    q25: Optional[float] = None
    q75: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


class AnomalyModelStatus(BaseModel):
    status: str = Field(..., description="'ready', 'uninitialized', or 'error'")
    model_version: str
    detector_name: str
    calibrated_threshold: float
    feature_count: int
    features: List[str]
    trained_at: Optional[str] = None
    baseline_summary: Optional[Dict[str, Any]] = None


class AnomalyPcapAnalysisResponse(BaseModel):
    status: str = Field(default="success")
    filename: str
    total_windows: int
    anomalous_windows: int
    overall_anomaly_score: float
    overall_prediction: str
    overall_severity: str
    window_results: List[AnomalyPredictionResult]
    top_deviations: List[AnomalyContributingFeature]
