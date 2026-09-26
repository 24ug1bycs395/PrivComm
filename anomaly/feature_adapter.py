"""Feature adapter for VPN Behavioral Anomaly Detection."""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from ml.anomaly.feature_extractor import extract_pcap_windows, extract_behavioral_features
from ml.anomaly.schemas import FEATURE_COLUMNS

logger = logging.getLogger("AnomalyFeatureAdapter")


def extract_features_from_pcap(pcap_path: str, window_sec: float = 60.0) -> List[Dict[str, Any]]:
    """Extract rolling time-window feature dictionaries from a PCAP file using Scapy."""
    if not Path(pcap_path).exists():
        raise FileNotFoundError(f"PCAP file not found: {pcap_path}")
    return extract_pcap_windows(pcap_path, window_seconds=window_sec)


def adapt_flow_features_to_behavioral(flow_features: Dict[str, Any]) -> Dict[str, float]:
    """
    Fallback adapter that maps single-flow / PCAP ingestion features to the 32 behavioral feature schema.
    Useful when single aggregate flow features are provided.
    """
    duration = float(flow_features.get("duration", 0.0) or flow_features.get("duration_sec", 0.0) or 1.0)
    pkt_count = float(flow_features.get("total_packets", 0) or flow_features.get("packet_count", 0))
    byte_count = float(flow_features.get("total_bytes", 0) or flow_features.get("byte_count", 0))

    pps = float(flow_features.get("packet_rate", 0.0) or (pkt_count / duration if duration > 0 else 0.0))
    bps = float(flow_features.get("byte_rate", 0.0) or (byte_count / duration if duration > 0 else 0.0))

    mean_pkt = float(flow_features.get("mean_packet_length", 0.0) or flow_features.get("mean_packet_size", 0.0) or (byte_count / pkt_count if pkt_count > 0 else 0.0))
    std_pkt = float(flow_features.get("std_packet_length", 0.0) or flow_features.get("std_packet_size", 0.0))
    min_pkt = float(flow_features.get("min_packet_length", 0.0) or flow_features.get("min_packet_size", 0.0))
    max_pkt = float(flow_features.get("max_packet_length", 0.0) or flow_features.get("max_packet_size", 0.0))

    mean_iat = float(flow_features.get("mean_iat", 0.0) or flow_features.get("mean_inter_arrival_time", 0.0))
    std_iat = float(flow_features.get("std_iat", 0.0) or flow_features.get("std_inter_arrival_time", 0.0))

    fwd_pkts = float(flow_features.get("fwd_packets", pkt_count * 0.5))
    bwd_pkts = float(flow_features.get("bwd_packets", pkt_count * 0.5))
    fwd_bytes = float(flow_features.get("fwd_bytes", byte_count * 0.5))
    bwd_bytes = float(flow_features.get("bwd_bytes", byte_count * 0.5))

    in_out_byte_ratio = fwd_bytes / bwd_bytes if bwd_bytes > 0 else 1.0
    in_out_pkt_ratio = fwd_pkts / bwd_pkts if bwd_pkts > 0 else 1.0

    return {
        "duration_sec": duration,
        "packet_count": pkt_count,
        "byte_count": byte_count,
        "packets_per_second": pps,
        "bytes_per_second": bps,
        "mean_packet_size": mean_pkt,
        "std_packet_size": std_pkt,
        "min_packet_size": min_pkt,
        "max_packet_size": max_pkt,
        "mean_inter_arrival_time": mean_iat,
        "std_inter_arrival_time": std_iat,
        "forward_packet_count": fwd_pkts,
        "backward_packet_count": bwd_pkts,
        "forward_byte_count": fwd_bytes,
        "backward_byte_count": bwd_bytes,
        "flow_count": float(flow_features.get("flow_count", 1.0)),
        "new_flows_per_minute": float(flow_features.get("new_flows_per_minute", 1.0)),
        "concurrent_flows": float(flow_features.get("concurrent_flows", 1.0)),
        "unique_source_count": float(flow_features.get("unique_source_count", 1.0)),
        "unique_destination_count": float(flow_features.get("unique_destination_count", 1.0)),
        "peer_count": float(flow_features.get("peer_count", 2.0)),
        "inbound_outbound_byte_ratio": in_out_byte_ratio,
        "inbound_outbound_packet_ratio": in_out_pkt_ratio,
        "tcp_packet_count": float(flow_features.get("tcp_packet_count", 0.0)),
        "udp_packet_count": float(flow_features.get("udp_packet_count", pkt_count)),
        "icmp_packet_count": float(flow_features.get("icmp_packet_count", 0.0)),
        "other_packet_count": float(flow_features.get("other_packet_count", 0.0)),
        "esp_packet_count": float(flow_features.get("esp_packet_count", pkt_count)),
        "ike_packet_count": float(flow_features.get("ike_packet_count", 0.0)),
        "sa_establishment_frequency": float(flow_features.get("sa_establishment_frequency", 0.0)),
        "session_duration_mean": duration,
        "session_duration_std": 0.0,
    }
