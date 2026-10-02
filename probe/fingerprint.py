"""Best-effort vendor fingerprinting from IKE vendor IDs and transforms."""

from typing import Any

VENDOR_SIGNATURES = {
    "strongSwan": "4a131c81",
    "Cisco ASA": "afcad713",
    "FortiGate": "8299031",
    "Libreswan": "4f456c6e",
}


def fingerprint_vendor(vendor_ids: list[str], transforms: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a vendor guess, confidence, and human-readable clues."""
    normalized = [value.lower().replace(" ", "") for value in vendor_ids]
    for vendor, signature in VENDOR_SIGNATURES.items():
        if any(value.startswith(signature) for value in normalized):
            return {
                "vendor": vendor,
                "confidence": 0.95,
                "clues": [f"Vendor ID prefix {signature}"],
            }
    if transforms:
        return {
            "vendor": "Unknown",
            "confidence": 0.1,
            "clues": ["IKE transforms were observed, but no known vendor signature matched."],
        }
    return {"vendor": "Unknown", "confidence": 0.0, "clues": []}
