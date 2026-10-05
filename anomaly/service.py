"""Service layer for VPN Behavioral Anomaly Detection."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np

from anomaly.feature_adapter import extract_features_from_pcap
from anomaly.model_loader import get_anomaly_artifact, get_anomaly_metadata
from anomaly.schemas import (
    AnomalyBaselineMetric,
    AnomalyContributingFeature,
    AnomalyModelStatus,
    AnomalyPcapAnalysisResponse,
    AnomalyPredictionResult,
)
from ml.anomaly.model import normalized_scores, raw_anomaly_scores
from ml.anomaly.schemas import FEATURE_COLUMNS

logger = logging.getLogger("AnomalyService")


def calculate_severity(score: float, is_anomalous: bool) -> str:
    if not is_anomalous or score < 0.40:
        return "LOW"
    elif score < 0.65:
        return "MEDIUM"
    elif score < 0.85:
        return "HIGH"
    else:
        return "CRITICAL"


def get_status() -> AnomalyModelStatus:
    """Return model status, feature schema, and threshold metadata."""
    try:
        art = get_anomaly_artifact()
        meta = get_anomaly_metadata()
        return AnomalyModelStatus(
            status="ready",
            model_version=art.get("model_version", "1.0.0"),
            detector_name=art.get("detector_name", "isolation_forest"),
            calibrated_threshold=round(float(art.get("threshold_raw", 0.0)), 4),
            feature_count=len(art.get("feature_columns", [])),
            features=art.get("feature_columns", []),
            trained_at=meta.get("training_completed_at"),
            baseline_summary=meta.get("training_summary"),
        )
    except Exception as e:
        logger.error(f"Failed to get anomaly model status: {e}")
        return AnomalyModelStatus(
            status="error",
            model_version="unknown",
            detector_name="unknown",
            calibrated_threshold=0.0,
            feature_count=len(FEATURE_COLUMNS),
            features=FEATURE_COLUMNS,
            baseline_summary={"error": str(e)},
        )


def get_baseline() -> List[AnomalyBaselineMetric]:
    """Return learned normal baseline metrics (median, IQR) for all 32 features."""
    art = get_anomaly_artifact()
    columns = art["feature_columns"]
    medians = art["baseline_median"]
    iqrs = art["baseline_iqr"]

    metrics = []
    for col, med, iqr in zip(columns, medians, iqrs, strict=False):
        metrics.append(AnomalyBaselineMetric(
            feature=col,
            median=round(float(med), 4),
            iqr=round(float(iqr), 4),
        ))
    return metrics


def extract_top_contributing(features: Dict[str, Any], artifact: Dict[str, Any], top_k: int = 5) -> List[AnomalyContributingFeature]:
    columns = artifact["feature_columns"]
    medians = np.asarray(artifact["baseline_median"], dtype=float)
    iqr = np.maximum(np.asarray(artifact["baseline_iqr"], dtype=float), 1e-9)
    values = np.asarray([float(features.get(col, 0.0)) for col in columns], dtype=float)
    deviations = np.abs((values - medians) / iqr)

    sorted_indices = np.argsort(deviations)[::-1][:top_k]
    result = []
    for idx in sorted_indices:
        val = float(values[idx])
        med = float(medians[idx])
        dev = float(deviations[idx])
        direction = "elevated above" if val > med else "depleted below"
        reason = f"{direction} normal baseline median ({med:.2f}) by {dev:.2f}x IQR"
        result.append(AnomalyContributingFeature(
            feature=columns[idx],
            value=round(val, 4),
            reason=reason,
            baseline_median=round(med, 4),
            baseline_iqr=round(float(iqr[idx]), 4),
        ))
    return result


def predict_sample(features: Dict[str, Any], top_k: int = 5) -> AnomalyPredictionResult:
    """Run anomaly detection inference on a single feature dictionary."""
    artifact = get_anomaly_artifact()
    columns = artifact["feature_columns"]

    # Fill any missing keys with 0.0
    feat_vector = np.asarray([[float(features.get(col, 0.0)) for col in columns]], dtype=float)
    raw = float(raw_anomaly_scores(artifact["detector"], artifact.get("scaler"), feat_vector)[0])
    norm_score = float(normalized_scores(np.asarray([raw]), artifact["score_center_raw"], artifact["score_scale_raw"])[0])
    is_anomaly = raw > float(artifact["threshold_raw"])
    prediction = "anomalous" if is_anomaly else "normal"
    score = round(norm_score, 4)
    severity = calculate_severity(score, is_anomaly)

    top_features = extract_top_contributing(features, artifact, top_k=top_k)

    return AnomalyPredictionResult(
        prediction=prediction,
        anomaly_score=score,
        severity=severity,
        detector=artifact.get("detector_name", "isolation_forest"),
        top_contributing_features=top_features,
        timestamp=features.get("timestamp"),
        window_duration_sec=float(features.get("duration_sec", 0.0)),
        packet_count=int(features.get("packet_count", 0)),
        byte_count=int(features.get("byte_count", 0)),
    )


def analyze_pcap_windows(pcap_path: str, window_sec: float = 60.0) -> AnomalyPcapAnalysisResponse:
    """Analyze a full PCAP file across rolling time windows."""
    get_anomaly_artifact()
    windows = extract_features_from_pcap(pcap_path, window_sec=window_sec)

    if not windows:
        # Single-window / empty fallback
        return AnomalyPcapAnalysisResponse(
            filename=pcap_path,
            total_windows=0,
            anomalous_windows=0,
            overall_anomaly_score=0.0,
            overall_prediction="normal",
            overall_severity="LOW",
            window_results=[],
            top_deviations=[],
        )

    results: List[AnomalyPredictionResult] = []
    all_deviations: Dict[str, AnomalyContributingFeature] = {}

    for win in windows:
        res = predict_sample(win, top_k=5)
        results.append(res)
        for cf in res.top_contributing_features:
            if cf.feature not in all_deviations or cf.value > all_deviations[cf.feature].value:
                all_deviations[cf.feature] = cf

    anom_count = sum(1 for r in results if r.prediction == "anomalous")
    max_score = max((r.anomaly_score for r in results), default=0.0)
    avg_score = float(np.mean([r.anomaly_score for r in results])) if results else 0.0
    overall_score = round(0.7 * max_score + 0.3 * avg_score, 4)
    overall_pred = "anomalous" if (anom_count > 0 or overall_score > 0.45) else "normal"
    overall_sev = calculate_severity(overall_score, overall_pred == "anomalous")

    # Sort aggregated deviations
    sorted_devs = sorted(all_deviations.values(), key=lambda d: abs(d.value - d.baseline_median) / max(d.baseline_iqr, 1e-9), reverse=True)[:5]

    return AnomalyPcapAnalysisResponse(
        filename=pcap_path,
        total_windows=len(windows),
        anomalous_windows=anom_count,
        overall_anomaly_score=overall_score,
        overall_prediction=overall_pred,
        overall_severity=overall_sev,
        window_results=results,
        top_deviations=sorted_devs,
    )
