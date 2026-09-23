import os
import json
import joblib
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

POSSIBLE_MODEL_DIRS = [
    os.path.join("traffic-classifier", "models"),
    "models",
    os.path.join("..", "traffic-classifier", "models")
]

def find_model_dir() -> str:
    """Find directory containing the trained model artifacts."""
    for d in POSSIBLE_MODEL_DIRS:
        if os.path.exists(os.path.join(d, "xgboost_traffic_classifier.json")) and \
           os.path.exists(os.path.join(d, "model_metadata.json")):
            return d
    raise FileNotFoundError(
        f"Could not locate model artifacts directory in search paths: {POSSIBLE_MODEL_DIRS}"
    )

def load_trained_model() -> Tuple[Any, Any, Dict[str, Any]]:
    """Load pre-trained XGBoost model, label encoder, and model metadata."""
    model_dir = find_model_dir()

    model_path = os.path.join(model_dir, "xgboost_traffic_classifier.json")
    encoder_path = os.path.join(model_dir, "label_encoder.joblib")
    metadata_path = os.path.join(model_dir, "model_metadata.json")

    from xgboost import XGBClassifier

    model = XGBClassifier()
    model.load_model(model_path)

    label_encoder = joblib.load(encoder_path)

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    logger.info(f"Loaded XGBoost model from {model_path}")
    return model, label_encoder, metadata
