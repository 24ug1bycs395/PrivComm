import logging
from typing import Any, Dict

import numpy as np

from ml.model_loader import load_trained_model

logger = logging.getLogger(__name__)

def predict_traffic_class(flow_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter for running inference using pre-trained XGBoost traffic classifier.
    Never alters trained model; aligns input feature vector exactly with training schema.
    """
    if not flow_features or len(flow_features) < 10:
        return {
            "status": "insufficient_features",
            "message": "Not enough network flow features to perform classification."
        }

    try:
        model, label_encoder, metadata = load_trained_model()
    except Exception as e:
        logger.error(f"Failed to load XGBoost model: {e}")
        return {
            "status": "model_error",
            "message": f"Failed to load trained model: {e}"
        }

    feature_cols = metadata["feature_columns"]
    classes = metadata["classes"]

    sample = dict(flow_features)

    # Compute engineered features if not already present
    if "bytes_per_pkt" not in sample:
        pkts_sec = float(sample.get("flowPktsPerSecond", 0))
        bytes_sec = float(sample.get("flowBytesPerSecond", 0))
        duration = float(sample.get("duration", 0))
        mean_fiat = float(sample.get("mean_fiat", 0))
        mean_biat = float(sample.get("mean_biat", 0))

        sample["bytes_per_pkt"] = bytes_sec / (pkts_sec + 1e-5)
        sample["fiat_biat_ratio"] = mean_fiat / (mean_biat + 1e-5)
        sample["log_duration"] = float(np.log1p(max(0.0, duration)))
        sample["log_bytes_sec"] = float(np.log1p(max(0.0, bytes_sec)))
        sample["log_pkts_sec"] = float(np.log1p(max(0.0, pkts_sec)))

    # Schema validation
    missing_cols = [col for col in feature_cols if col not in sample]
    if missing_cols:
        logger.warning(f"Missing required feature columns: {missing_cols}")
        return {
            "status": "insufficient_features",
            "missing_features": missing_cols
        }

    input_vector = np.array([[float(sample[col]) for col in feature_cols]])

    try:
        probas = model.predict_proba(input_vector)[0]
        top_idx = int(np.argmax(probas))
        traffic_type = classes[top_idx]
        confidence = float(round(probas[top_idx], 4))

        return {
            "status": "success",
            "traffic_type": traffic_type,
            "confidence": confidence,
            "probabilities": {classes[i]: float(round(probas[i], 4)) for i in range(len(classes))}
        }
    except Exception as e:
        logger.error(f"Inference execution failed: {e}")
        return {
            "status": "inference_error",
            "message": str(e)
        }
