"""Tests for the dependency-free packet decoder."""

import random
import struct

import pytest

from analyzer.pcap_decoder import decode_pcap


def _ike_packet() -> bytes:
    spi = bytes.fromhex("0102030405060708")
    header = spi + b"\x00" * 8 + bytes([0, 0x20, 34, 0x08]) + struct.pack("!II", 0, 28)
    return header


def _ethernet_udp_ike() -> bytes:
    ip = bytes([0x45, 0, 0, 56, 0, 1, 0, 0, 64, 17, 0, 0])
    ip += bytes([192, 168, 1, 2, 192, 168, 1, 1])
    udp = struct.pack("!HHHH", 500, 500, 36, 0)
    return b"\x00" * 12 + struct.pack("!H", 0x0800) + ip + udp + _ike_packet()


def test_pcap_ike_packet(tmp_path) -> None:
    packet = _ethernet_udp_ike()
    path = tmp_path / "sample.pcap"
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    record = struct.pack("<IIII", 1, 2, len(packet), len(packet)) + packet
    path.write_bytes(header + record)
    result = decode_pcap(str(path))
    assert result.file_format == "PCAP"
    assert result.ike_packets[0].ike_version == "IKEv2"
    assert result.ike_packets[0].initiator_spi == "0102030405060708"
    assert result.ike_packets[0].exchange_type == 34
    assert result.ike_packets[0].frame_number == 1
    assert result.ike_packets[0].capture_byte_offset == 82
    assert result.packet_evidence[0]["fields"]["ike_version"] == {
        "value": "IKEv2",
        "capture_byte_offset": 99,
        "capture_byte_length": 1,
    }


def test_pcapng_epb(tmp_path) -> None:
    packet = _ethernet_udp_ike()
    shb = struct.pack("<IIQHHI", 0x0A0D0D0A, 28, 0x1A2B3C4D, 1, 0, 28) + struct.pack("<I", 28)
    idb = struct.pack("<IIHHII", 1, 20, 1, 0, 65535, 20)
    padded = packet + b"\x00" * ((4 - len(packet) % 4) % 4)
    block_length = 32 + len(padded)
    epb = struct.pack("<IIIIIII", 6, block_length, 0, 0, 1, len(packet), len(packet)) + padded
    epb += struct.pack("<I", block_length)
    path = tmp_path / "sample.pcapng"
    path.write_bytes(shb + idb + epb)
    result = decode_pcap(str(path))
    assert result.file_format == "PCAPNG"
    assert result.packet_count == 1
    assert len(result.ike_packets) == 1
    assert result.ike_packets[0].capture_byte_offset == 118
    assert result.ike_packets[0].frame_number == 1


def test_pcap_esp_evidence_offsets(tmp_path) -> None:
    ip = bytes([0x45, 0, 0, 28, 0, 1, 0, 0, 64, 50, 0, 0])
    ip += bytes([192, 0, 2, 1, 192, 0, 2, 2])
    esp = struct.pack("!II", 0x01020304, 7) + b"\x00" * 4
    packet = b"\x00" * 12 + struct.pack("!H", 0x0800) + ip + esp
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    record = struct.pack("<IIII", 1, 0, len(packet), len(packet)) + packet
    path = tmp_path / "esp.pcap"
    path.write_bytes(header + record)

    result = decode_pcap(str(path))

    assert result.esp_packets[0].capture_byte_offset == 74
    assert result.esp_packets[0].spi_byte_offset == 74
    assert result.esp_packets[0].sequence_byte_offset == 78
    assert result.packet_evidence[0]["fields"]["sequence_number"] == {
        "value": 7,
        "capture_byte_offset": 78,
        "capture_byte_length": 4,
    }


def test_truncated_pcap_record_header_is_rejected(tmp_path) -> None:
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    path = tmp_path / "truncated.pcap"
    path.write_bytes(header + b"\x00" * 7)

    with pytest.raises(ValueError, match="header is incomplete"):
        decode_pcap(str(path))


def test_decoder_handles_deterministic_malformed_packet_sweep(tmp_path) -> None:
    rng = random.Random(20260614)
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    records = []
    for index in range(128):
        payload = bytearray(rng.randbytes(rng.randrange(0, 96)))
        if len(payload) >= 14:
            payload[12:14] = struct.pack("!H", 0x0800)
        if len(payload) >= 15:
            payload[14] = (payload[14] & 0x0F) | 0x40
        records.append(struct.pack("<IIII", index, 0, len(payload), len(payload)) + payload)
    path = tmp_path / "malformed-sweep.pcap"
    path.write_bytes(header + b"".join(records))

    result = decode_pcap(str(path))

    assert result.packet_count == 128


def test_unrecognized_magic_raises(tmp_path) -> None:
    path = tmp_path / "bad.pcap"
    path.write_bytes(b"BAD!" + b"\x00" * 40)
    with pytest.raises(ValueError):
        decode_pcap(str(path))
