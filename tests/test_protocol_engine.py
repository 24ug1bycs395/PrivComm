"""
Comprehensive test script for ProtocolIdentificationEngine and FastAPI POST /analyze/protocol.
Generates synthetic standard IPsec PCAP captures and validates extraction logic end-to-end.
"""

import os
import tempfile
from fastapi.testclient import TestClient
from scapy.all import Ether, IP, IPv6, UDP, Raw, wrpcap
try:
    from scapy.layers.ipsec import ESP
except ImportError:
    ESP = None

from main import app
from services.protocol_engine import ProtocolIdentificationEngine

client = TestClient(app)


def create_test_ipsec_pcap() -> str:
    """
    Creates a synthetic standard IKEv2 + ESP PCAP file:
    - IPv4 source 192.168.1.10 -> 10.0.0.1
    - UDP 500 (IKEv2) packet with SA payload proposing AES-256-GCM, DH Group 14
    - ESP packets with sequence tracking
    """
    temp_pcap = tempfile.NamedTemporaryFile(delete=False, suffix=".pcap")
    pcap_path = temp_pcap.name
    temp_pcap.close()

    packets = []

    # 1. Construct IKEv2 Init Packet
    # Header: Init SPI (8B), Resp SPI (8B), Next Payload (1B), Vers (1B: 0x20), Exchange (1B), Flags (1B), MsgID (4B), Len (4B)
    init_spi = b"\x11\x22\x33\x44\x55\x66\x77\x88"
    resp_spi = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    next_payload = 33  # Security Association (SA)
    version = 0x20     # IKEv2 (Major 2, Minor 0)
    exchange = 34      # IKE_SA_INIT
    flags = 0x08       # Initiator
    msg_id = (0).to_bytes(4, byteorder="big")

    # SA Payload with Proposal & Transforms
    # Transform 1: ENCR AES-GCM-16 (ID 20) with 256-bit key length
    # Header: last (0), reserved (0), length (12), type (1), id (20)
    t1 = bytes([0, 0, 0, 12, 1, 0, 0, 20, 0x80, 14, 0x01, 0x00]) # Attr 14 = 256 bits (0x0100)
    # Transform 4: DH Group 14 (MODP 2048)
    t2 = bytes([0, 0, 0, 8, 4, 0, 0, 14])

    transforms = t1 + t2
    # Proposal: last (0), reserved (0), length (8 + len(transforms)), prop_num (1), proto_id (1: IKE), spi_size (0), num_transforms (2)
    prop_len = 8 + len(transforms)
    proposal = bytes([0, 0, (prop_len >> 8) & 0xFF, prop_len & 0xFF, 1, 1, 0, 2]) + transforms

    # SA Payload Header: next_payload (0), reserved (0), length (4 + len(proposal))
    sa_len = 4 + len(proposal)
    sa_payload = bytes([0, 0, (sa_len >> 8) & 0xFF, sa_len & 0xFF]) + proposal

    total_len = 28 + len(sa_payload)
    # Header: init_spi(8) + resp_spi(8) + next_payload(1) + version(1) + exchange(1) + flags(1) + msg_id(4) + total_len(4)
    ike_header = init_spi + resp_spi + bytes([next_payload, version, exchange, flags]) + msg_id + total_len.to_bytes(4, byteorder="big")
    ike_data = ike_header + sa_payload

    pkt1 = Ether() / IP(src="192.168.1.10", dst="10.0.0.1") / UDP(sport=500, dport=500) / Raw(load=ike_data)
    packets.append(pkt1)

    # 2. Add an ESP packet (IP Proto 50)
    # ESP Header: SPI (4B), Sequence Number (4B), Payload Data
    esp_data = b"\x00\x00\x10\x00" + (1).to_bytes(4, byteorder="big") + b"\xde\xad\xbe\xef" * 8
    pkt2 = Ether() / IP(src="192.168.1.10", dst="10.0.0.1", proto=50) / Raw(load=esp_data)
    packets.append(pkt2)

    wrpcap(pcap_path, packets)
    return pcap_path


def test_engine_and_endpoint():
    pcap_path = create_test_ipsec_pcap()
    print(f"[TEST] Created synthetic PCAP at: {pcap_path}")

    try:
        # Test Direct Engine
        engine = ProtocolIdentificationEngine()
        result = engine.analyze_pcap(pcap_path)
        print("\n--- Direct Engine Result ---")
        print(result.model_dump_json(indent=2))

        assert result.ipsec_detected is True
        assert result.ike_version == "IKEv2"
        assert result.esp_detected is True
        assert result.mode == "Tunnel"
        assert result.replay_protection is True
        assert result.ip_version == "IPv4"
        assert result.source_ip == "192.168.1.10"
        assert result.destination_ip == "10.0.0.1"

        # Test FastAPI Endpoint
        with open(pcap_path, "rb") as f:
            response = client.post(
                "/analyze/protocol",
                files={"pcap_file": ("test_tunnel.pcap", f, "application/vnd.tcpdump.pcap")}
            )

        print("\n--- FastAPI Endpoint Response ---")
        print(f"Status: {response.status_code}")
        print(response.json())

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["ipsec_detected"] is True
        assert json_data["ike_version"] == "IKEv2"
        assert json_data["esp_detected"] is True
        assert json_data["mode"] == "Tunnel"

        print("\n[SUCCESS] All verification tests passed flawlessly!")

    finally:
        if os.path.exists(pcap_path):
            os.remove(pcap_path)


if __name__ == "__main__":
    test_engine_and_endpoint()
