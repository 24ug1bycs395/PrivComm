"""FastAPI routes for analysis integrity seals and certificates."""

import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seal.attestation import generate_certificate
from seal.engine import AuditSeal, seal_analysis, verify_seal

router = APIRouter(prefix="/seal", tags=["Cryptographic Audit Seals"])


class SealCreateRequest(BaseModel):
    analysis_id: str
    findings: list[dict[str, Any]] = Field(default_factory=list)


class SealVerifyRequest(BaseModel):
    seal_id: str
    findings: list[dict[str, Any]] = Field(default_factory=list)


class SealAttestRequest(BaseModel):
    seal_id: str
    analysis_meta: dict[str, Any] = Field(default_factory=dict)


def _load_seal(seal_id: str) -> AuditSeal:
    safe_name = os.path.basename(seal_id)
    path = os.path.join("seals", f"{safe_name}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Seal '{seal_id}' not found")
    try:
        with open(path, encoding="utf-8") as handle:
            return AuditSeal(**json.load(handle))
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=500, detail="Stored seal is invalid") from exc


@router.post("/create", summary="Create a signed Merkle audit seal")
async def create_seal(request: SealCreateRequest) -> dict[str, Any]:
    return seal_analysis({"analysis_id": request.analysis_id}, request.findings).to_dict()


@router.post("/verify", summary="Verify a signed Merkle audit seal")
async def verify_created_seal(request: SealVerifyRequest) -> dict[str, Any]:
    seal = _load_seal(request.seal_id)
    valid, detail = verify_seal(seal, request.findings)
    return {"valid": valid, "detail": detail, "seal": seal.to_dict()}


@router.post("/attest", summary="Generate a compliance certificate from a seal")
async def attest_seal(request: SealAttestRequest) -> dict[str, Any]:
    seal = _load_seal(request.seal_id)
    certificate = generate_certificate(seal, request.analysis_meta)
    valid, _ = verify_seal(seal, request.analysis_meta.get("findings", []))
    certificate["status"] = "VALID" if valid else "TAMPERED"
    return certificate


@router.get("/public-key", summary="Get the current audit seal public key")
async def get_public_key() -> dict[str, str]:
    from seal.signer import load_keypair
    _, public_key = load_keypair()
    return {"public_key": public_key.hex(), "algorithm": "ED25519"}
