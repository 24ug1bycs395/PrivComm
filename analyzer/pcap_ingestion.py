import hashlib
import logging
import os

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from typing import Any, Dict, Tuple

from analyzer.esp_parser import parse_esp_scapy, parse_esp_tshark_json
from analyzer.flow_extractor import extract_flow_features_scapy
from analyzer.ike_parser import parse_ike_scapy, parse_ike_tshark_json
from analyzer.ipsec_parser import synthesize_ipsec_config
from analyzer.metadata_exposure import analyze_metadata_exposure
from analyzer.tshark import find_tshark_path, run_tshark_json

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pcap", ".pcapng"}

def validate_pcap_file(pcap_path: str) -> Tuple[bool, str]:
    """Validate PCAP file existence and file extension."""
    if not os.path.exists(pcap_path):
        return False, f"File not found: '{pcap_path}'"

    ext = os.path.splitext(pcap_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file format '{ext}'. Must be .pcap or .pcapng"

    if os.path.getsize(pcap_path) == 0:
        return False, f"File '{pcap_path}' is empty (0 bytes)."

    return True, "Valid PCAP file"

def ingest_and_parse_pcap(pcap_path: str) -> Dict[str, Any]:
    """
    Main PCAP ingestion function.
    Safely parses PCAP using TShark if available, falling back to Scapy.
    Returns parsed IPsec configuration, packet metadata, and flow features.
    """
    valid, msg = validate_pcap_file(pcap_path)
    if not valid:
        return {
            "status": "error",
            "message": msg,
            "ipsec": {"detected": False},
            "flow_features": {},
            "packet_count": 0,
            "source_ip": None,
            "destination_ip": None,
            "ip_version": "IPv4",
            "metadata_exposure": {}
        }

    zdp_result = None
    decoder_error = None
    capture_sha256 = hashlib.sha256()
    with open(pcap_path, "rb") as capture_file:
        for chunk in iter(lambda: capture_file.read(1024 * 1024), b""):
            capture_sha256.update(chunk)
    try:
        from analyzer.pcap_decoder import decode_pcap
        zdp_result = decode_pcap(pcap_path)
        logger.info(
            "[ZDP] Pure-Python decoder: %d IKE pkts, %d ESP pkts",
            len(zdp_result.ike_packets),
            len(zdp_result.esp_packets),
        )
    except Exception as exc:
        decoder_error = str(exc)
        logger.warning("[ZDP] Pure-Python decoder failed: %s, continuing with Scapy/TShark", exc)

    # Attempt Scapy parsing for direct feature extraction and packet analysis (cap to 5000 pkts to prevent memory spikes)
    scapy_pkts = None
    try:
        from scapy.all import rdpcap
        scapy_pkts = rdpcap(pcap_path, count=5000)
    except Exception as e:
        logger.warning(f"Scapy failed to parse '{pcap_path}': {e}")

    # Check TShark availability
    tshark_bin = find_tshark_path()
    tshark_json = None

    if tshark_bin:
        logger.info(f"Using TShark at {tshark_bin} for dissection...")
        tshark_json = run_tshark_json(pcap_path, display_filter="isakmp or esp or ah")
        if tshark_json:
            ike_info = parse_ike_tshark_json(tshark_json)
            esp_info = parse_esp_tshark_json(tshark_json)
            packet_count = len(tshark_json)
        else:
            ike_info = parse_ike_scapy(scapy_pkts) if scapy_pkts else {}
            esp_info = parse_esp_scapy(scapy_pkts) if scapy_pkts else {}
            packet_count = len(scapy_pkts) if scapy_pkts else 0
    else:
        logger.info("TShark binary not found in PATH; using Scapy parser engine...")
        if scapy_pkts is not None:
            ike_info = parse_ike_scapy(scapy_pkts)
            esp_info = parse_esp_scapy(scapy_pkts)
            packet_count = len(scapy_pkts)
        else:
            return {
                "status": "error",
                "message": "Neither TShark nor Scapy could parse the PCAP file.",
                "ipsec": {"detected": False},
                "flow_features": {},
                "packet_count": 0,
                "source_ip": None,
                "destination_ip": None,
                "ip_version": "IPv4",
                "metadata_exposure": {}
            }

    ipsec_config = synthesize_ipsec_config(ike_info, esp_info)
    if zdp_result is not None:
        first_ike = zdp_result.ike_packets[0] if zdp_result.ike_packets else None
        if first_ike:
            for key, value in {
                "ike_version": first_ike.ike_version,
                "initiator_spi": first_ike.initiator_spi,
                "responder_spi": first_ike.responder_spi,
                "exchange_type": first_ike.exchange_name,
            }.items():
                if not ike_info.get(key) or ike_info.get(key) == "unknown":
                    ike_info[key] = value
            ike_info["proposals"] = first_ike.proposals
        if not esp_info.get("esp_packet_count"):
            esp_info["esp_packet_count"] = len(zdp_result.esp_packets)
        if not esp_info.get("observed_spis"):
            esp_info["observed_spis"] = sorted(zdp_result.unique_spis)
        if not esp_info.get("esp_detected") and zdp_result.esp_packets:
            esp_info["esp_detected"] = True
        ipsec_config = synthesize_ipsec_config(ike_info, esp_info)
        ipsec_config["esp_spi_list"] = sorted(zdp_result.unique_spis)
        ipsec_config["esp_packet_count"] = len(zdp_result.esp_packets)
    flow_features = extract_flow_features_scapy(scapy_pkts) if scapy_pkts else {}
    meta_exposure = analyze_metadata_exposure(
        packets=scapy_pkts,
        tshark_packets=tshark_json,
        ike_info=ike_info,
        esp_info=esp_info,
        ipsec_config=ipsec_config
    )

    return {
        "status": "success",
        "filename": os.path.basename(pcap_path),
        "filepath": os.path.abspath(pcap_path),
        "packet_count": packet_count,
        "ipsec": ipsec_config,
        "flow_features": flow_features,
        "source_ip": meta_exposure.get("source_ip"),
        "destination_ip": meta_exposure.get("destination_ip"),
        "ip_version": meta_exposure.get("ip_version", "IPv4"),
        "metadata_exposure": meta_exposure,
        "zdp_used": zdp_result is not None,
        "capture_sha256": capture_sha256.hexdigest(),
        "packet_evidence": zdp_result.packet_evidence if zdp_result is not None else [],
        "decoder_error": decoder_error,
        "zdp_esp_packets": [
            {
                "timestamp": packet.timestamp,
                "src_ip": packet.src_ip,
                "dst_ip": packet.dst_ip,
                "spi": packet.spi,
                "sequence_number": packet.sequence_number,
                "payload_length": packet.payload_length,
            }
            for packet in (zdp_result.esp_packets if zdp_result is not None else [])
        ],
    }
