"""Compliance certificate representation for a verified audit seal."""

import secrets
import string
from datetime import datetime, timezone
from typing import Any

from seal.engine import AuditSeal


def generate_certificate(seal: AuditSeal, analysis_meta: dict[str, Any]) -> dict[str, Any]:
    """Return a certificate payload suitable for storage or export."""
    alphabet = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(alphabet) for _ in range(6))
    return {
        "certificate_id": f"PC-CERT-{code}",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "issued_for": analysis_meta.get("filename", "unknown"),
        "seal_id": seal.seal_id,
        "merkle_root": seal.merkle_root,
        "signature": seal.signature,
        "public_key": seal.public_key,
        "verification_instructions": (
            "Re-run POST /seal/verify with this certificate's seal_id to confirm integrity."
        ),
        "status": "UNVERIFIED",
    }
