import os
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from typing import Dict, Any, Tuple

from analyzer.tshark import find_tshark_path, run_tshark_json
from analyzer.ike_parser import parse_ike_scapy, parse_ike_tshark_json
from analyzer.esp_parser import parse_esp_scapy, parse_esp_tshark_json
from analyzer.ipsec_parser import synthesize_ipsec_config
from analyzer.flow_extractor import extract_flow_features_scapy

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
            "packet_count": 0
        }

    # Attempt Scapy parsing for direct feature extraction and packet analysis
    scapy_pkts = None
    try:
        from scapy.all import rdpcap
        scapy_pkts = rdpcap(pcap_path)
    except Exception as e:
        logger.warning(f"Scapy failed to parse '{pcap_path}': {e}")

    # Check TShark availability
    tshark_bin = find_tshark_path()

    if tshark_bin:
        logger.info(f"Using TShark at {tshark_bin} for dissection...")
        tshark_json = run_tshark_json(pcap_path)
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
                "packet_count": 0
            }

    ipsec_config = synthesize_ipsec_config(ike_info, esp_info)
    flow_features = extract_flow_features_scapy(scapy_pkts) if scapy_pkts else {}

    return {
        "status": "success",
        "filename": os.path.basename(pcap_path),
        "filepath": os.path.abspath(pcap_path),
        "packet_count": packet_count,
        "ipsec": ipsec_config,
        "flow_features": flow_features
    }
