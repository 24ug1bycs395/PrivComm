"""Tests for RFC 4303 length arithmetic."""

from analyzer.rfc4303 import eliminate_impossible_ciphers, is_consistent_with_cipher


def _packet(total_length: int) -> dict[str, int]:
    return {"payload_length": total_length}


def test_cipher_profiles_accept_valid_lengths() -> None:
    assert is_consistent_with_cipher(56, "AES-256-GCM-16")[0]
    assert is_consistent_with_cipher(44, "AES-256-CBC")[0]
    assert is_consistent_with_cipher(28, "3DES-CBC")[0]


def test_cipher_profiles_reject_invalid_lengths() -> None:
    assert not is_consistent_with_cipher(53, "AES-256-CBC")[0]
    assert not is_consistent_with_cipher(27, "3DES-CBC")[0]


def test_gcm_consistent_packets_eliminate_cbc() -> None:
    packets = [_packet(84), _packet(100), _packet(116)]
    result = eliminate_impossible_ciphers(packets, ["AES-256-GCM-16", "3DES-CBC"])
    assert "AES-256-GCM-16" in result.viable_ciphers
    assert "3DES-CBC" in result.eliminated_ciphers


def test_confidence_bands() -> None:
    assert eliminate_impossible_ciphers([], ["AES-256-GCM-16"]).confidence == 0.3
    assert eliminate_impossible_ciphers([_packet(84)] * 3, ["AES-256-GCM-16"]).confidence == 0.65
    assert eliminate_impossible_ciphers([_packet(84)] * 10, ["AES-256-GCM-16"]).confidence == 0.85
    assert eliminate_impossible_ciphers([_packet(84)] * 50, ["AES-256-GCM-16"]).confidence == 0.98
