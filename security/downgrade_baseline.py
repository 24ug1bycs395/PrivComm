"""Explicit, capture-backed per-tunnel configuration baselines."""

import hmac
import json
import os
import tempfile
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict

BASELINE_PATH = os.getenv("IPSEC_BASELINES_PATH", os.path.join("config", "tunnel_baselines.json"))
_LOCK = RLock()
_TRACKED_FIELDS = (
    "ike_version",
    "encryption",
    "key_length",
    "dh_group",
    "pfs",
    "mode",
    "integrity",
    "prf",
    "replay_protection",
)
_CLASSICAL_STRENGTH = {
    "1": 56, "2": 80, "5": 80, "14": 112, "15": 128, "16": 152,
    "19": 128, "20": 192, "21": 256, "28": 128, "31": 224,
}
_ENCRYPTION_STRENGTH = (
    ("NULL", -1),
    ("3DES", 1),
    ("DES", 0),
    ("AES-128-CBC", 2),
    ("AES-256-CBC", 3),
    ("AES-128-GCM", 4),
    ("AES-256-GCM", 5),
)


def _is_known(value: Any) -> bool:
    return value is not None and str(value).strip().lower() not in {"", "unknown", "none"}


def baseline_record_authorized(supplied_token: str | None) -> bool:
    """Check the separate operator secret required by the baseline-recording API."""
    expected = os.environ.get("IPSEC_BASELINE_AUTH_SECRET", "").encode("utf-8")
    supplied = (supplied_token or "").encode("utf-8")
    return len(expected) >= 32 and hmac.compare_digest(expected, supplied)


def _canonical_tunnel_id(tunnel_id: str) -> str:
    normalized = tunnel_id.strip()
    if not normalized or len(normalized) > 128:
        raise ValueError("tunnel_id must contain 1 to 128 non-whitespace characters.")
    return normalized


def _read_baselines(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as baseline_file:
            data = json.load(baseline_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read tunnel baseline store '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Tunnel baseline store '{path}' must contain a JSON object.")
    return data


def record_tunnel_baseline(
    tunnel_id: str,
    ipsec_config: Dict[str, Any],
    capture_sha256: str,
    path: str = BASELINE_PATH,
) -> Dict[str, Any]:
    """Persist an explicitly requested baseline from an analyzed capture."""
    key = _canonical_tunnel_id(tunnel_id)
    if len(capture_sha256) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in capture_sha256):
        raise ValueError("A valid 64-character capture SHA-256 is required to record a baseline.")
    observed = {field: ipsec_config.get(field) for field in _TRACKED_FIELDS}
    entry = {
        "tunnel_id": key,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "capture_sha256": capture_sha256.lower(),
        "observed": observed,
    }
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with _LOCK:
        baselines = _read_baselines(path)
        baselines[key] = entry
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=".tunnel-baselines-", suffix=".tmp", dir=parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as temp_file:
                json.dump(baselines, temp_file, indent=2, sort_keys=True)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temporary_path, path)
        except OSError:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
            raise
    return entry


def _strength(field: str, value: Any) -> int | None:
    text = str(value).strip().upper()
    if field == "ike_version":
        if text.startswith("IKEV1"):
            return 1
        if text.startswith("IKEV2"):
            return 2
    elif field == "encryption":
        for name, rank in _ENCRYPTION_STRENGTH:
            if name in text:
                return rank
    elif field == "dh_group":
        return _CLASSICAL_STRENGTH.get(text)
    elif field in {"pfs", "replay_protection"}:
        if value is True or text in {"ENFORCED", "YES", "TRUE", "ENABLED"}:
            return 1
        if value is False or text in {"DISABLED", "NO", "FALSE"}:
            return 0
    elif field == "mode":
        if text == "TUNNEL":
            return 1
        if text == "TRANSPORT":
            return 0
    elif field == "integrity" or field == "prf":
        if "MD5" in text:
            return 0
        if "SHA1" in text:
            return 1
        if "SHA2" in text or "AEAD" in text or "SHA-2" in text:
            return 2
    elif field == "key_length":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def compare_tunnel_baseline(
    tunnel_id: str,
    ipsec_config: Dict[str, Any],
    path: str = BASELINE_PATH,
) -> Dict[str, Any]:
    """Compare known observations and mark downgrade only where ordering is defined."""
    key = _canonical_tunnel_id(tunnel_id)
    with _LOCK:
        baseline = _read_baselines(path).get(key)
    if baseline is None:
        return {
            "tunnel_id": key,
            "status": "NO_BASELINE",
            "downgrade_detected": False,
            "field_comparisons": [],
        }
    if not isinstance(baseline, dict) or not isinstance(baseline.get("observed"), dict):
        raise ValueError(f"Stored baseline for tunnel '{key}' is malformed.")

    comparisons = []
    for field in _TRACKED_FIELDS:
        previous = baseline["observed"].get(field)
        current = ipsec_config.get(field)
        if not _is_known(previous) or not _is_known(current):
            comparisons.append({
                "field": field,
                "status": "INSUFFICIENT_EVIDENCE",
                "baseline": previous,
                "observed": current,
            })
            continue
        if str(previous).strip().lower() == str(current).strip().lower():
            status = "UNCHANGED"
        else:
            previous_strength = _strength(field, previous)
            current_strength = _strength(field, current)
            if previous_strength is not None and current_strength is not None:
                status = "DOWNGRADE" if current_strength < previous_strength else "CHANGE_NOT_DOWNGRADE"
            else:
                status = "CHANGED_NOT_RANKED"
        comparisons.append({
            "field": field,
            "status": status,
            "baseline": previous,
            "observed": current,
        })

    downgrade_detected = any(item["status"] == "DOWNGRADE" for item in comparisons)
    comparable = any(
        item["status"] in {"UNCHANGED", "DOWNGRADE", "CHANGE_NOT_DOWNGRADE"}
        for item in comparisons
    )
    return {
        "tunnel_id": key,
        "baseline_recorded_at": baseline.get("recorded_at"),
        "baseline_capture_sha256": baseline.get("capture_sha256"),
        "status": (
            "DOWNGRADE" if downgrade_detected
            else "NO_DOWNGRADE" if comparable
            else "INSUFFICIENT_EVIDENCE"
        ),
        "downgrade_detected": downgrade_detected,
        "field_comparisons": comparisons,
    }
