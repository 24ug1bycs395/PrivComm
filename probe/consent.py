"""Signed, short-lived consent checks for explicitly authorized probes."""

import base64
import hashlib
import hmac
import ipaddress
import json
import os
import time
from typing import Any

from probe.allowlist import is_allowed

_SECRET_ENV = "PROBE_CONSENT_SECRET"
_MIN_SECRET_BYTES = 32
_MIN_TTL_SECONDS = 30
_MAX_TTL_SECONDS = 3600


def _secret() -> bytes:
    secret = os.environ.get(_SECRET_ENV, "").encode("utf-8")
    if len(secret) < _MIN_SECRET_BYTES:
        raise ValueError(
            f"{_SECRET_ENV} must be configured with at least {_MIN_SECRET_BYTES} bytes."
        )
    return secret


def _encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def create_consent_token(target_ip: str, ttl_seconds: int = 300) -> str:
    """Create an operator-side token scoped to one IP address and short expiry."""
    target = str(ipaddress.ip_address(target_ip))
    if not _MIN_TTL_SECONDS <= ttl_seconds <= _MAX_TTL_SECONDS:
        raise ValueError(
            f"Consent token lifetime must be between {_MIN_TTL_SECONDS} "
            f"and {_MAX_TTL_SECONDS} seconds."
        )
    payload = json.dumps(
        {"target": target, "expires_at": int(time.time()) + ttl_seconds},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = _encode(payload)
    signature = hmac.new(
        _secret(), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def _decode_payload(encoded_payload: str) -> dict[str, Any]:
    padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
    payload = base64.urlsafe_b64decode(padded.encode("ascii"))
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("Consent token payload must be an object.")
    return decoded


def check_double_barrier(target_ip: str, consent_token: str) -> tuple[bool, str]:
    """Require valid signed consent for this IP and an exact allowlist entry."""
    try:
        target = str(ipaddress.ip_address(target_ip))
        encoded_payload, encoded_signature = consent_token.split(".", 1)
        supplied_signature = base64.urlsafe_b64decode(
            (encoded_signature + "=" * (-len(encoded_signature) % 4)).encode("ascii")
        )
        expected_signature = hmac.new(
            _secret(), encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return False, "Invalid probe authorization signature."
        payload = _decode_payload(encoded_payload)
        if payload.get("target") != target:
            return False, "Probe authorization does not cover the target IP."
        expires_at = payload.get("expires_at")
        if not isinstance(expires_at, int) or expires_at <= int(time.time()):
            return False, "Probe authorization has expired or is malformed."
    except (ValueError, UnicodeError, json.JSONDecodeError):
        return False, "Invalid or unavailable probe authorization."

    if not is_allowed(target):
        return False, "Target IP is not present in the probe allowlist."
    return True, "Signed authorization and allowlist checks passed."
