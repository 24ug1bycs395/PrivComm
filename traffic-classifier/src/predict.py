"""
Inference Script for Encrypted Traffic Multiclass Classifier.
Accepts flow feature vectors (via JSON file or inline string),
validates feature schema, and outputs class predictions, confidence,
full class probability distributions, and feature explainability metrics.
"""

import argparse
import json
import os
import sys

import joblib
import numpy as np

try:
    from xgboost import XGBClassifier
    XGBOOST_INSTALLED = True
except ImportError:
    XGBOOST_INSTALLED = False
    XGBClassifier = None


def load_model_artifacts(models_dir: str = "models", model_type: str = "xgboost"):
    if model_type == "random_forest":
        model_filename = "random_forest_model.joblib"
    else:
        model_filename = "xgboost_traffic_classifier.json"

    model_path = os.path.join(models_dir, model_filename)

    # Smart fallback if models_dir points to wrong location
    if not os.path.exists(model_path):
        if os.path.exists(os.path.join("models", model_filename)):
            models_dir = "models"
            model_path = os.path.join(models_dir, model_filename)
        elif os.path.exists(os.path.join("..", "models", model_filename)):
            models_dir = os.path.join("..", "models")
            model_path = os.path.join(models_dir, model_filename)

    encoder_path = os.path.join(models_dir, "label_encoder.joblib")
    metadata_path = os.path.join(models_dir, "model_metadata.json")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file missing at: {model_path}. Run train.py first.")
    if not os.path.exists(encoder_path):
        raise FileNotFoundError(f"Label encoder missing at: {encoder_path}.")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Model metadata missing at: {metadata_path}.")

    if model_type == "random_forest":
        model = joblib.load(model_path)
    else:
        model = XGBClassifier()
        model.load_model(model_path)

    le = joblib.load(encoder_path)

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    return model, le, metadata


def predict_sample(sample_dict: dict, models_dir: str = "models", model_type: str = "xgboost") -> dict:
    model, le, metadata = load_model_artifacts(models_dir, model_type=model_type)
    feature_cols = metadata["feature_columns"]
    classes = metadata["classes"]

    # Auto-compute engineered features if raw features were provided
    if "bytes_per_pkt" not in sample_dict:
        bytes_sec = float(sample_dict.get("flowBytesPerSecond", 0))
        pkts_sec = float(sample_dict.get("flowPktsPerSecond", 0))
        duration = float(sample_dict.get("duration", 0))
        mean_fiat = float(sample_dict.get("mean_fiat", 0))
        mean_biat = float(sample_dict.get("mean_biat", 0))

        sample_dict["bytes_per_pkt"] = bytes_sec / (pkts_sec + 1e-5)
        sample_dict["fiat_biat_ratio"] = mean_fiat / (mean_biat + 1e-5)
        sample_dict["log_duration"] = float(np.log1p(max(0, duration)))
        sample_dict["log_bytes_sec"] = float(np.log1p(max(0, bytes_sec)))
        sample_dict["log_pkts_sec"] = float(np.log1p(max(0, pkts_sec)))

    # Schema validation
    missing_feats = [col for col in feature_cols if col not in sample_dict]
    if missing_feats:
        raise KeyError(f"Input sample missing required feature columns: {missing_feats}")

    # Build input feature vector in EXACT model training column order
    input_vector = np.array([[float(sample_dict[col]) for col in feature_cols]])

    # Run inference
    probas = model.predict_proba(input_vector)[0]
    top_class_idx = int(np.argmax(probas))
    top_class_name = classes[top_class_idx]
    top_confidence = float(round(probas[top_class_idx], 4))

    # Probability distribution across all classes sorted by confidence
    prob_dist = {}
    sorted_indices = np.argsort(probas)[::-1]
    for idx in sorted_indices:
        prob_dist[classes[idx]] = float(round(probas[idx], 4))

    # Explainability: Top contributing features
    feature_importances = getattr(model, "feature_importances_", np.zeros(len(feature_cols)))
    feat_contribs = []
    for idx, col in enumerate(feature_cols):
        feat_contribs.append({
            "feature": col,
            "val": float(sample_dict[col]),
            "importance": float(round(feature_importances[idx], 4))
        })
    feat_contribs = sorted(feat_contribs, key=lambda x: x["importance"], reverse=True)[:5]

    result = {
        "model_used": model_type,
        "prediction": top_class_name,
        "confidence": top_confidence,
        "probabilities": prob_dist,
        "top_contributing_features": feat_contribs
    }

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run inference on network flow sample.")
    parser.add_argument("--input", type=str, help="Path to JSON file containing sample features")
    parser.add_argument("--json", type=str, help="Inline JSON string containing sample features")
    parser.add_argument("--models-dir", type=str, default="models", help="Directory containing model artifacts")
    parser.add_argument("--model", type=str, choices=["xgboost", "random_forest"], default="xgboost", help="Model to use (xgboost or random_forest)")
    parser.add_argument("--sample", action="store_true", help="Use a sample vector for quick testing")
    args = parser.parse_args()

    sample_dict = None

    if args.input:
        with open(args.input, "r") as f:
            sample_dict = json.load(f)
    elif args.json:
        sample_dict = json.loads(args.json)
    elif args.sample:
        # Benchmark sample vector
        sample_dict = {
            "duration": 143704195.0,
            "total_fiat": 143704195.0,
            "total_biat": 42106019.0,
            "min_fiat": 64.0,
            "min_biat": 20.0,
            "max_fiat": 101572528.0,
            "max_biat": 382847.0,
            "mean_fiat": 101674.9,
            "mean_biat": 53919.1,
            "flowPktsPerSecond": 8.54,
            "flowBytesPerSecond": 1610.0,
            "min_flowiat": 19.0,
            "max_flowiat": 101572528.0,
            "mean_flowiat": 117473.7,
            "std_flowiat": 137463.7,
            "min_active": -1.0,
            "mean_active": 0.0,
            "max_active": -1.0,
            "std_active": 0.0,
            "min_idle": -1.0,
            "mean_idle": 0.0,
            "max_idle": 101572528.0,
            "std_idle": 0.0
        }
    else:
        print("[!] No input provided. Use --input sample.json, --json '{...}', or --sample.")
        sys.exit(1)

    output = predict_sample(sample_dict, models_dir=args.models_dir, model_type=args.model)
    print("\n--- Model Prediction Result ---")
    print(json.dumps(output, indent=4))
