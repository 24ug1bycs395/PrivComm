"""Train and serialize the VPN behavioral anomaly detector.

Only NORMAL rows are used to fit either detector. Anomalous scenarios are
reserved for validation/test measurement and never influence the learned
normal boundary except through detector selection on the validation split.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import joblib
import pandas as pd

from ml.anomaly.model import build_bundle, fit_detector, normalized_scores, raw_anomaly_scores
from ml.anomaly.schemas import FEATURE_COLUMNS, SCHEMA_VERSION, validate_dataframe

SEED = 42


def _scenario_time_split(frame: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by within-scenario order to avoid neighboring-window leakage."""
    ordered = frame.sort_values(["scenario_type", "timestamp", "sample_id"]).reset_index(drop=True)
    train_parts, validation_parts, test_parts = [], [], []
    for _, group in ordered.groupby("scenario_type", sort=True):
        n = len(group)
        if group["label"].iloc[0] == 0:
            train_end = max(1, int(n * 0.60))
            validation_end = max(train_end + 1, int(n * 0.80)) if n > 2 else n
            train_parts.append(group.iloc[:train_end])
            validation_parts.append(group.iloc[train_end:validation_end])
            test_parts.append(group.iloc[validation_end:])
        else:
            validation_end = max(1, int(n * 0.50))
            validation_parts.append(group.iloc[:validation_end])
            test_parts.append(group.iloc[validation_end:])
    train = pd.concat(train_parts, ignore_index=True)
    validation = pd.concat(validation_parts, ignore_index=True)
    test = pd.concat(test_parts, ignore_index=True)
    if train.empty or validation.empty or test.empty:
        raise ValueError("Dataset is too small for scenario/time-aware train/validation/test splits")
    if not (train["label"] == 0).all():
        raise ValueError("Training split contains anomalous labels; normal-only training was not preserved")
    return train, validation, test


def _evaluate_candidate(candidate: Dict[str, object], frame: pd.DataFrame) -> Dict[str, object]:
    matrix = frame[FEATURE_COLUMNS].to_numpy(dtype=float)
    raw = raw_anomaly_scores(candidate["detector"], candidate.get("scaler"), matrix)
    scores = normalized_scores(raw, candidate["score_center_raw"], candidate["score_scale_raw"])
    predictions = (raw > candidate["threshold_raw"]).astype(int)
    from ml.anomaly.evaluate import evaluate_predictions
    return evaluate_predictions(frame["label"].to_numpy(), predictions, scores, frame["scenario_type"])


def train_detector(dataset_path: str, model_dir: str, reports_dir: str, seed: int = SEED) -> Dict[str, object]:
    frame = validate_dataframe(pd.read_csv(dataset_path))
    if not (frame["scenario_type"] == "normal").any():
        raise ValueError("Dataset must include NORMAL rows for unsupervised training")
    train, validation, test = _scenario_time_split(frame)
    train_matrix = train[FEATURE_COLUMNS].to_numpy(dtype=float)
    validation_normal = validation[validation["label"] == 0]
    calibration_matrix = (validation_normal if not validation_normal.empty else train)[FEATURE_COLUMNS].to_numpy(dtype=float)

    candidates = {}
    candidate_metrics = {}
    for name in ("isolation_forest", "robust_zscore"):
        detector, scaler = fit_detector(name, train_matrix, seed=seed)
        bundle = build_bundle(name, detector, scaler, FEATURE_COLUMNS, train_matrix, calibration_matrix)
        candidates[name] = bundle
        candidate_metrics[name] = _evaluate_candidate(bundle, validation)

    selected_name = max(candidate_metrics, key=lambda name: (candidate_metrics[name]["f1"], -candidate_metrics[name]["false_positive_rate"]))
    selected = candidates[selected_name]
    test_metrics = _evaluate_candidate(selected, test)

    output_model = Path(model_dir) / "vpn_anomaly_detector.joblib"
    output_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected, output_model)

    metadata = {
        "model_name": "VPN Behavioral Anomaly Detector",
        "model_version": "1.0.0",
        "training_dataset_version": SCHEMA_VERSION,
        "features": FEATURE_COLUMNS,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "training_method": "normal-only unsupervised training with scenario/time-aware holdout",
        "training_data_sources": sorted(frame.get("data_source", pd.Series(["unspecified"])).astype(str).unique().tolist()),
        "synthetic_data_warning": bool(frame.get("data_source", pd.Series(dtype=str)).astype(str).eq("synthetic_controlled").any()),
        "selected_detector": selected_name,
        "candidates": ["isolation_forest", "robust_zscore"],
        "score_definition": "0.0 is strongly consistent with the learned normal baseline; 1.0 is strongly anomalous. This is a calibrated ranking score, not a probability.",
        "training_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "normal_training_rows": int(len(train)),
        "validation_metrics": candidate_metrics,
        "test_metrics": test_metrics,
    }
    model_dir_path = Path(model_dir)
    (model_dir_path / "feature_schema.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "label_mapping": {"0": "normal", "1": "anomalous"},
    }, indent=2), encoding="utf-8")
    (model_dir_path / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    (reports_path / "evaluation.json").write_text(json.dumps({
        "selected_detector": selected_name,
        "validation": candidate_metrics,
        "test": test_metrics,
        "split_note": "Rows were ordered within each scenario by timestamp; anomalous scenarios were never included in the normal-only fit.",
    }, indent=2), encoding="utf-8")
    (reports_path / "model_card.json").write_text(json.dumps({
        "schema_version": "privcomm.model-card.v1",
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"],
        "task": "VPN behavioral anomaly detection",
        "training_dataset_version": SCHEMA_VERSION,
        "training_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "training_data_sources": metadata["training_data_sources"],
        "synthetic_data_warning": metadata["synthetic_data_warning"],
        "features": FEATURE_COLUMNS,
        "split_method": metadata["training_method"],
        "selected_detector": selected_name,
        "validation_metrics": candidate_metrics[selected_name],
        "test_metrics": test_metrics,
        "score_definition": metadata["score_definition"],
        "limitations": [
            "The split holds out later rows within scenario types, not independently collected captures or sites.",
            "Synthetic controlled data, when present, does not establish production generalization.",
            "The anomaly score is a ranking score, not a probability.",
            "False-positive rates must be interpreted with the checked-in dataset and reported test support.",
        ],
    }, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f"Saved model artifact to {output_model}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train VPN behavioral anomaly detector")
    parser.add_argument("--dataset", default="ml/anomaly/datasets/vpn_behavioral_dataset.csv")
    parser.add_argument("--model-dir", default="ml/anomaly/models")
    parser.add_argument("--reports-dir", default="ml/anomaly/reports")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    train_detector(args.dataset, args.model_dir, args.reports_dir, args.seed)


if __name__ == "__main__":
    main()
