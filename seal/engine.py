"""Creation and verification of tamper-evident analysis seals."""

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from seal.merkle import merkle_root
from seal.signer import load_keypair, sign, verify

logger = logging.getLogger(__name__)
SEALS_DIR = "seals"


@dataclass
class AuditSeal:
    """Persisted cryptographic seal metadata."""

    seal_id: str
    analysis_id: str
    sealed_at: str
    leaf_hashes: list[str]
    merkle_root: str
    signature: str
    public_key: str
    algorithm: str = "SHA256-MERKLE+ED25519"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _finding_leaves(
    analysis_id: str, sealed_at: str, findings: list[dict[str, Any]]
) -> list[bytes]:
    leaves = [hashlib.sha256(_canonical(finding)).digest() for finding in findings]
    leaves.append(hashlib.sha256(_canonical({
        "analysis_id": analysis_id,
        "sealed_at": sealed_at,
        "finding_count": len(findings),
    })).digest())
    return leaves


def seal_analysis(analysis_result: dict[str, Any], findings: list[dict[str, Any]]) -> AuditSeal:
    """Create, persist, and return a signed Merkle seal."""
    analysis_id = str(analysis_result.get("analysis_id") or analysis_result.get("id") or "unknown")
    sealed_at = datetime.now(timezone.utc).isoformat()
    leaves = _finding_leaves(analysis_id, sealed_at, findings)
    root = merkle_root(leaves)
    private_key, public_key = load_keypair()
    signature = sign(private_key, root)
    seal = AuditSeal(
        seal_id=f"PC-SEAL-{analysis_id}-{int(time.time() * 1000)}",
        analysis_id=analysis_id,
        sealed_at=sealed_at,
        leaf_hashes=[leaf.hex() for leaf in leaves],
        merkle_root=root.hex(),
        signature=signature.hex(),
        public_key=public_key.hex(),
    )
    os.makedirs(SEALS_DIR, exist_ok=True)
    with open(os.path.join(SEALS_DIR, f"{seal.seal_id}.json"), "w", encoding="utf-8") as handle:
        json.dump(seal.to_dict(), handle, indent=2)
    logger.info("Created analysis seal %s", seal.seal_id)
    return seal


def verify_seal(seal: AuditSeal, findings: list[dict[str, Any]]) -> tuple[bool, str]:
    """Recompute finding leaves and verify root signature."""
    leaves = _finding_leaves(seal.analysis_id, seal.sealed_at, findings)
    root = merkle_root(leaves)
    if root.hex() != seal.merkle_root:
        logger.info("Seal verification failed: Merkle root mismatch for %s", seal.seal_id)
        return False, "Merkle root mismatch: findings or seal metadata changed."
    valid = verify(bytes.fromhex(seal.public_key), root, bytes.fromhex(seal.signature))
    detail = (
        "Seal signature and Merkle root are valid."
        if valid
        else "Ed25519 signature verification failed."
    )
    logger.info("Verified seal %s: %s", seal.seal_id, valid)
    return valid, detail
