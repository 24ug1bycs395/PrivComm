"""Model helpers shared by training, evaluation, and inference."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class RobustZScoreDetector:
    """A transparent baseline using median and IQR learned from normal data."""

    def fit(self, matrix: np.ndarray) -> "RobustZScoreDetector":
        self.median_ = np.median(matrix, axis=0)
        q1, q3 = np.percentile(matrix, [25, 75], axis=0)
        # Constant normal features still carry signal, but a 1e-9 denominator
        # would make every deviation numerically infinite and destroy score
        # resolution. Keep a small domain-scaled tolerance instead.
        self.scale_ = np.maximum(q3 - q1, np.maximum(np.abs(self.median_) * 0.05, 1.0))
        return self

    def score_samples(self, matrix: np.ndarray) -> np.ndarray:
        robust_z = np.abs((matrix - self.median_) / self.scale_)
        return np.max(robust_z, axis=1)


def fit_detector(name: str, matrix: np.ndarray, seed: int = 42) -> Tuple[object, object]:
    """Fit one detector and return (detector, optional scaler)."""
    if name == "isolation_forest":
        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix)
        detector = IsolationForest(
            n_estimators=300,
            max_samples="auto",
            contamination="auto",
            random_state=seed,
            n_jobs=-1,
        )
        detector.fit(scaled)
        return detector, scaler
    if name == "robust_zscore":
        return RobustZScoreDetector().fit(matrix), None
    raise ValueError(f"Unknown detector: {name}")


def raw_anomaly_scores(detector: object, scaler: object, matrix: np.ndarray) -> np.ndarray:
    if scaler is not None:
        matrix = scaler.transform(matrix)
    if isinstance(detector, IsolationForest):
        return -detector.decision_function(matrix)
    return detector.score_samples(matrix)


def normalized_scores(raw_scores: np.ndarray, center: float, scale: float) -> np.ndarray:
    return np.clip((raw_scores - center) / max(scale, 1e-9), 0.0, 1.0)


def build_bundle(
    detector_name: str,
    detector: object,
    scaler: object,
    feature_columns: list[str],
    train_matrix: np.ndarray,
    calibration_normal_matrix: np.ndarray,
) -> Dict[str, object]:
    calibration_raw = raw_anomaly_scores(detector, scaler, calibration_normal_matrix)
    center = float(np.median(calibration_raw))
    scale = float(max(np.percentile(calibration_raw, 99) - center, 1e-9))
    threshold = float(np.percentile(calibration_raw, 95))
    median = np.median(train_matrix, axis=0)
    q1, q3 = np.percentile(train_matrix, [25, 75], axis=0)
    baseline_iqr = np.maximum(q3 - q1, np.maximum(np.abs(median) * 0.05, 1.0))
    return {
        "artifact_type": "vpn_behavioral_anomaly_detector",
        "artifact_version": "1.0.0",
        "detector_name": detector_name,
        "detector": detector,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "threshold_raw": threshold,
        "score_center_raw": center,
        "score_scale_raw": scale,
        "baseline_median": median.tolist(),
        "baseline_iqr": baseline_iqr.tolist(),
    }
