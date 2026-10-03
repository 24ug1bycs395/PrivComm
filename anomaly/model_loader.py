"""Model loader and cache for VPN Behavioral Anomaly Detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger("AnomalyModelLoader")

# Search paths for anomaly models
DEFAULT_SEARCH_PATHS = [
    Path(__file__).parent.parent / "ml" / "anomaly" / "models" / "vpn_anomaly_detector.joblib",
    Path("ml/anomaly/models/vpn_anomaly_detector.joblib"),
    Path(__file__).parent / "models" / "vpn_anomaly_detector.joblib",
]

_CACHED_ARTIFACT: Optional[Dict[str, Any]] = None
_CACHED_METADATA: Optional[Dict[str, Any]] = None


def find_anomaly_model_path() -> Optional[Path]:
    for p in DEFAULT_SEARCH_PATHS:
        if p.exists():
            return p.resolve()
    return None


def get_anomaly_artifact(model_path: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
    global _CACHED_ARTIFACT
    if _CACHED_ARTIFACT is not None and not force_reload and model_path is None:
        return _CACHED_ARTIFACT

    path = Path(model_path) if model_path else find_anomaly_model_path()
    if not path or not path.exists():
        raise FileNotFoundError(f"VPN Behavioral Anomaly model not found. Checked: {[str(p) for p in DEFAULT_SEARCH_PATHS]}")

    logger.info(f"Loading VPN behavioral anomaly model from: {path}")
    artifact = joblib.load(path)
    if not isinstance(artifact, dict) or artifact.get("artifact_type") != "vpn_behavioral_anomaly_detector":
        raise ValueError(f"Invalid artifact format in {path}")

    if model_path is None:
        _CACHED_ARTIFACT = artifact

    return artifact


def get_anomaly_metadata(metadata_path: Optional[str] = None) -> Dict[str, Any]:
    global _CACHED_METADATA
    if _CACHED_METADATA is not None and metadata_path is None:
        return _CACHED_METADATA

    meta_paths = [
        Path(__file__).parent.parent / "ml" / "anomaly" / "models" / "model_metadata.json",
        Path("ml/anomaly/models/model_metadata.json"),
    ]
    if metadata_path:
        meta_paths.insert(0, Path(metadata_path))

    for p in meta_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if metadata_path is None:
                    _CACHED_METADATA = data
                return data

    # Fallback to reconstructing from loaded artifact
    art = get_anomaly_artifact()
    return {
        "model_version": art.get("model_version", "1.0.0"),
        "detector_name": art.get("detector_name", "isolation_forest"),
        "calibrated_threshold": art.get("threshold_raw", 0.0),
        "features": art.get("feature_columns", []),
    }
