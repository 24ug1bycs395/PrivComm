"""Evaluation helpers and CLI for VPN behavioral anomaly detectors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from ml.anomaly.model import normalized_scores, raw_anomaly_scores
from ml.anomaly.schemas import FEATURE_COLUMNS, validate_dataframe


def evaluate_predictions(
    labels: np.ndarray,
    predictions: np.ndarray,
    scores: np.ndarray,
    scenarios: pd.Series,
) -> Dict[str, object]:
    """Return anomaly metrics, false-positive rate, and scenario breakdown."""
    cm = confusion_matrix(labels, predictions, labels=[0, 1]).tolist()
    normal_count = max(1, int(np.sum(labels == 0)))
    false_positives = int(np.sum((labels == 0) & (predictions == 1)))
    by_scenario = {}
    for scenario in sorted(scenarios.astype(str).unique()):
        mask = scenarios.astype(str).to_numpy() == scenario
        by_scenario[scenario] = {
            "samples": int(np.sum(mask)),
            "anomaly_rate_detected": float(np.mean(predictions[mask] == 1)),
            "mean_anomaly_score": float(np.mean(scores[mask])),
            "recall": float(recall_score(labels[mask], predictions[mask], zero_division=0)) if np.any(labels[mask] == 1) else None,
        }
    return {
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "false_positive_rate": float(false_positives / normal_count),
        "confusion_matrix_labels_0_normal_1_anomalous": cm,
        "anomaly_score_distribution": {
            "min": float(np.min(scores)),
            "median": float(np.median(scores)),
            "p95": float(np.percentile(scores, 95)),
            "max": float(np.max(scores)),
        },
        "per_scenario": by_scenario,
    }


def evaluate_frame(frame: pd.DataFrame, artifact: Dict[str, object]) -> Dict[str, object]:
    frame = validate_dataframe(frame)
    matrix = frame[FEATURE_COLUMNS].to_numpy(dtype=float)
    raw = raw_anomaly_scores(artifact["detector"], artifact.get("scaler"), matrix)
    scores = normalized_scores(raw, artifact["score_center_raw"], artifact["score_scale_raw"])
    predictions = (raw > float(artifact["threshold_raw"])).astype(int)
    return evaluate_predictions(frame["label"].to_numpy(), predictions, scores, frame["scenario_type"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a VPN behavioral anomaly artifact")
    parser.add_argument("--dataset", default="ml/anomaly/datasets/vpn_behavioral_dataset.csv")
    parser.add_argument("--model", default="ml/anomaly/models/vpn_anomaly_detector.joblib")
    parser.add_argument("--output", default="ml/anomaly/reports/evaluation.json")
    args = parser.parse_args()
    report = evaluate_frame(pd.read_csv(args.dataset), joblib.load(args.model))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
