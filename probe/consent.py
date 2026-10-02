"""Double-barrier consent checks for active network probing."""

import hashlib

from probe.allowlist import is_allowed


def check_double_barrier(target_ip: str, consent_token: str) -> tuple[bool, str]:
    """Require both the target-specific token and an exact allowlist entry."""
    expected = hashlib.sha256(
        f"PRIVCOMM-PROBE-CONSENT:{target_ip}".encode("utf-8")
    ).hexdigest()
    if consent_token != expected:
        return False, "Invalid consent token for target IP."
    if not is_allowed(target_ip):
        return False, "Target IP is not present in the probe allowlist."
    return True, "Consent and allowlist checks passed."
