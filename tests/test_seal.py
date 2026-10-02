"""Tests for Merkle and Ed25519 audit seals."""

from seal.attestation import generate_certificate
from seal.engine import seal_analysis, verify_seal
from seal.merkle import merkle_proof, merkle_root, sha256, verify_proof


def test_merkle_roots_are_deterministic() -> None:
    for count in (1, 2, 3, 4, 5):
        leaves = [sha256(str(index).encode()) for index in range(count)]
        assert merkle_root(leaves) == merkle_root(leaves)


def test_merkle_proofs_verify() -> None:
    leaves = [sha256(str(index).encode()) for index in range(4)]
    root = merkle_root(leaves)
    for index, leaf in enumerate(leaves):
        assert verify_proof(leaf, merkle_proof(leaves, index), root)


def test_seal_round_trip_and_tamper_detection(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    findings = [{"finding_id": "F-1", "severity": "LOW", "title": "Example"}]
    seal = seal_analysis({"analysis_id": "analysis-1"}, findings)
    assert verify_seal(seal, findings)[0]
    findings[0]["severity"] = "HIGH"
    assert not verify_seal(seal, findings)[0]


def test_certificate_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seal = seal_analysis({"analysis_id": "analysis-2"}, [])
    certificate = generate_certificate(seal, {"filename": "capture.pcap"})
    required = {
        "certificate_id", "issued_at", "issued_for", "seal_id", "merkle_root",
        "signature", "public_key", "status",
    }
    assert required.issubset(certificate)
