import os
import tempfile

from scapy.all import IP, UDP, Ether, Raw, wrpcap

from analyzer.metadata_exposure import (
    _analyze_spi_correlation,
    _analyze_transport_mode_exposure,
    _extract_endpoint_ips,
)
from services.protocol_engine import ProtocolIdentificationEngine


def create_sample_pcap(src="192.168.1.50", dst="10.0.0.99") -> str:
    temp_pcap = tempfile.NamedTemporaryFile(delete=False, suffix=".pcap")
    path = temp_pcap.name
    temp_pcap.close()

    pkt1 = Ether() / IP(src=src, dst=dst) / UDP(sport=500, dport=500) / Raw(load=b"\x00" * 32)
    pkt2 = Ether() / IP(src=src, dst=dst, proto=50) / Raw(load=b"\x00\x00\x12\x34\x00\x00\x00\x01data")
    wrpcap(path, [pkt1, pkt2])
    return path


def test_extract_endpoint_ips():
    pcap_path = create_sample_pcap("192.168.1.100", "10.0.0.200")
    try:
        from scapy.all import rdpcap
        pkts = rdpcap(pcap_path)
        src, dst, ip_ver, unique_srcs, unique_dsts = _extract_endpoint_ips(packets=pkts)
        assert src == "192.168.1.100"
        assert dst == "10.0.0.200"
        assert ip_ver == "IPv4"
        assert "192.168.1.100" in unique_srcs
        assert "10.0.0.200" in unique_dsts
    finally:
        if os.path.exists(pcap_path):
            os.remove(pcap_path)


def test_analyze_spi_correlation():
    ike_info = {"initiator_spi": "1122334455667788", "responder_spi": "8877665544332211"}
    esp_info = {"observed_spis": ["0x00001000"]}
    spi_res = _analyze_spi_correlation(ike_info, esp_info)
    assert spi_res["initiator_spi"] == "1122334455667788"
    assert spi_res["spi_linkability_risk"] in ["MEDIUM", "HIGH"]
    assert spi_res["session_tracking_vulnerability"] is True


def test_transport_mode_exposure():
    res_transport = _analyze_transport_mode_exposure("Transport", "IPv4")
    assert res_transport["exposure_risk"] == "HIGH"
    assert res_transport["inner_header_exposed"] is True
    assert res_transport["exposed_metadata_bytes_per_pkt"] == 20

    res_tunnel = _analyze_transport_mode_exposure("Tunnel", "IPv4")
    assert res_tunnel["exposure_risk"] == "LOW"
    assert res_tunnel["inner_header_exposed"] is False
    assert res_tunnel["exposed_metadata_bytes_per_pkt"] == 0


def test_full_metadata_exposure_analysis():
    pcap_path = create_sample_pcap("192.168.1.10", "10.0.0.1")
    try:
        engine = ProtocolIdentificationEngine()
        result = engine.analyze_pcap(pcap_path)

        assert result.source_ip == "192.168.1.10"
        assert result.destination_ip == "10.0.0.1"
        assert result.metadata_exposure is not None
        assert result.metadata_exposure["source_ip"] == "192.168.1.10"
        assert result.metadata_exposure["destination_ip"] == "10.0.0.1"
        assert "visible_endpoints" in result.metadata_exposure
        assert "spi_correlation" in result.metadata_exposure
        assert "transport_mode_exposure" in result.metadata_exposure
    finally:
        if os.path.exists(pcap_path):
            os.remove(pcap_path)
