"""Exact-match target allowlist for active IKE probes."""

import json
import os
from datetime import datetime, timezone
from typing import Any

ALLOWLIST_FILE = "probe_allowlist.json"


def _load() -> list[dict[str, Any]]:
    if not os.path.exists(ALLOWLIST_FILE):
        with open(ALLOWLIST_FILE, "w", encoding="utf-8") as handle:
            json.dump([], handle)
        return []
    try:
        with open(ALLOWLIST_FILE, encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save(entries: list[dict[str, Any]]) -> None:
    with open(ALLOWLIST_FILE, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)


def is_allowed(target_ip: str) -> bool:
    """Return true only when target_ip exactly matches an allowlist entry."""
    return any(entry.get("ip") == target_ip for entry in _load())


def add_to_allowlist(target_ip: str, added_by: str, reason: str) -> None:
    """Add or replace an exact IP allowlist entry."""
    entries = [entry for entry in _load() if entry.get("ip") != target_ip]
    entries.append({
        "ip": target_ip,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "added_by": added_by,
        "reason": reason,
    })
    _save(entries)


def remove_from_allowlist(target_ip: str) -> None:
    """Remove an exact IP allowlist entry if it exists."""
    _save([entry for entry in _load() if entry.get("ip") != target_ip])


def list_allowlist() -> list[dict[str, Any]]:
    """Return a copy of the current exact-match allowlist."""
    return list(_load())
