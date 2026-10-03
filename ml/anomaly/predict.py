"""Application-facing inference interface for VPN behavioral anomalies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import joblib
import numpy as np

from ml.anomaly.feature_extractor import extract_pcap_windows
from ml.anomaly.model import normalized_scores, raw_anomaly_scores

DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "vpn_anomaly_detector.joblib"


def load_artifact(model_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"VPN anomaly model artifact not found: {path}")
    artifact = joblib.load(path)
    if artifact.get("artifact_type") != "vpn_behavioral_anomaly_detector":
        raise ValueError(f"Unsupported anomaly model artifact: {path}")
    return artifact


def _contributing_features(features: Mapping[str, Any], artifact: Dict[str, Any], top_k: int) -> list[dict]:
    columns = artifact["feature_columns"]
    medians = np.asarray(artifact["baseline_median"], dtype=float)
    iqr = np.maximum(np.asarray(artifact["baseline_iqr"], dtype=float), 1e-9)
    values = np.asarray([float(features[column]) for column in columns], dtype=float)
    deviations = np.abs((values - medians) / iqr)
    result = []
    for index in np.argsort(deviations)[::-1][:top_k]:
        direction = "above" if values[index] > medians[index] else "below"
        result.append({
            "feature": columns[index],
            "value": float(values[index]),
            "reason": f"{direction} the learned normal median by {deviations[index]:.2f} IQR",
            "baseline_median": float(medians[index]),
            "baseline_iqr": float(iqr[index]),
        })
    return result


def predict(features: Mapping[str, Any], model_path: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """Predict normal/anomalous from one behavioral feature mapping.

    The score is a calibrated ranking score, not a probability. 0 means the
    observation is consistent with the learned normal baseline; 1 means it is
    strongly outside the calibrated normal range.
    """
    artifact = load_artifact(model_path)
    missing = [column for column in artifact["feature_columns"] if column not in features]
    if missing:
        raise ValueError(f"Missing behavioral features: {missing}")
    vector = np.asarray([[float(features[column]) for column in artifact["feature_columns"]]], dtype=float)
    if not np.isfinite(vector).all():
        raise ValueError("Behavioral features must be finite numbers")
    raw = float(raw_anomaly_scores(artifact["detector"], artifact.get("scaler"), vector)[0])
    score = float(normalized_scores(np.asarray([raw]), artifact["score_center_raw"], artifact["score_scale_raw"])[0])
    prediction = "anomalous" if raw > artifact["threshold_raw"] else "normal"
    return {
        "prediction": prediction,
        "anomaly_score": round(score, 6),
        "top_contributing_features": _contributing_features(features, artifact, top_k),
        "detector": artifact["detector_name"],
        "score_definition": "Calibrated ranking score from 0 (normal-consistent) to 1 (strongly anomalous); not a probability.",
    }


def predict_pcap(pcap_path: str, model_path: Optional[str] = None) -> list[Dict[str, Any]]:
    """Extract windows from a PCAP and run the same production inference path."""
    return [predict(window, model_path=model_path) for window in extract_pcap_windows(pcap_path)]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run VPN behavioral anomaly inference")
    parser.add_argument("--model", default=None)
    parser.add_argument("--features", help="JSON object containing the behavioral feature mapping")
    parser.add_argument("--pcap", help="PCAP/PCAPNG path to extract and score")
    args = parser.parse_args()
    if args.pcap:
        print(json.dumps(predict_pcap(args.pcap, args.model), indent=2))
    elif args.features:
        print(json.dumps(predict(json.loads(args.features), args.model), indent=2))
    else:
        parser.error("provide --features or --pcap")


if __name__ == "__main__":
    main()
