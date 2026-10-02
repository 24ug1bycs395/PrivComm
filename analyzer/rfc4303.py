"""RFC 4303 ESP length arithmetic for eliminating impossible ciphers."""

from dataclasses import asdict, dataclass
from typing import Any

CIPHER_PROFILES = {
    "AES-256-GCM-16": {"block_size": 1, "iv_len": 8, "icv_len": 16, "stream": True},
    "AES-128-GCM-16": {"block_size": 1, "iv_len": 8, "icv_len": 16, "stream": True},
    "AES-256-GCM-8": {"block_size": 1, "iv_len": 8, "icv_len": 8, "stream": True},
    "AES-256-CBC": {"block_size": 16, "iv_len": 16, "icv_len": 12, "stream": False},
    "AES-128-CBC": {"block_size": 16, "iv_len": 16, "icv_len": 12, "stream": False},
    "3DES-CBC": {"block_size": 8, "iv_len": 8, "icv_len": 12, "stream": False},
    "ChaCha20-Poly1305": {"block_size": 1, "iv_len": 8, "icv_len": 16, "stream": True},
}


@dataclass
class CipherEliminationResult:
    """Result of testing candidate ciphers against all observed ESP packets."""

    input_ciphers: list[str]
    viable_ciphers: list[str]
    eliminated_ciphers: list[str]
    elimination_reasons: dict[str, list[str]]
    sample_size: int
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


def _esp_payload_len(esp_packet_total_len: int, ip_header_len: int = 20) -> int:
    """Return bytes after the ESP SPI and sequence header."""
    return esp_packet_total_len - ip_header_len - 8


def _packet_length(packet: Any) -> int:
    if isinstance(packet, dict):
        return int(packet.get("payload_length", 0))
    return int(getattr(packet, "payload_length", 0))


def is_consistent_with_cipher(payload_len: int, cipher_name: str) -> tuple[bool, str]:
    """Check whether an ESP payload length is possible for a cipher profile."""
    profile = CIPHER_PROFILES.get(cipher_name)
    if profile is None:
        return False, f"Unknown cipher profile: {cipher_name}"
    if payload_len < profile["iv_len"] + profile["icv_len"]:
        return False, "Payload is shorter than IV plus integrity tag."
    ciphertext_len = payload_len - profile["iv_len"] - profile["icv_len"]
    if not profile["stream"] and ciphertext_len % profile["block_size"]:
        return False, (
            f"Ciphertext region length {ciphertext_len} is not aligned to "
            f"{profile['block_size']} bytes."
        )
    return True, "Length is consistent with the cipher profile."


def eliminate_impossible_ciphers(
    esp_packets: list[Any],
    candidate_ciphers: list[str] | None = None,
    min_packets: int = 3,
) -> CipherEliminationResult:
    """Eliminate a cipher if any observed ESP packet is length-inconsistent."""
    candidates = list(candidate_ciphers or CIPHER_PROFILES)
    reasons: dict[str, list[str]] = {}
    viable: list[str] = []
    for cipher in candidates:
        cipher_reasons: list[str] = []
        for index, packet in enumerate(esp_packets):
            payload_len = _esp_payload_len(_packet_length(packet))
            consistent, reason = is_consistent_with_cipher(payload_len, cipher)
            if not consistent:
                cipher_reasons.append(f"Packet {index + 1}: {reason}")
        if cipher_reasons:
            reasons[cipher] = cipher_reasons
        else:
            viable.append(cipher)
    sample_size = len(esp_packets)
    confidence = (
        0.3 if sample_size < 3 else 0.65 if sample_size < 10
        else 0.85 if sample_size < 50 else 0.98
    )
    eliminated = [cipher for cipher in candidates if cipher not in viable]
    return CipherEliminationResult(
        candidates, viable, eliminated, reasons, sample_size, confidence
    )
