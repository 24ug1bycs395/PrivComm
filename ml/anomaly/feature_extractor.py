"""Extract observable behavioral features from Scapy packet collections."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


def _layer(packet: Any, name: str) -> Any:
    try:
        return packet.getlayer(name)
    except Exception:
        return None


def _ip_endpoints(packet: Any) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    ip = _layer(packet, "IP") or _layer(packet, "IPv6")
    if ip is None:
        return None, None, None
    return getattr(ip, "src", None), getattr(ip, "dst", None), getattr(ip, "proto", None)


def _packet_record(packet: Any) -> Dict[str, Any]:
    src, dst, proto = _ip_endpoints(packet)
    tcp = _layer(packet, "TCP")
    udp = _layer(packet, "UDP")
    if tcp is not None:
        protocol, src_port, dst_port = "tcp", int(tcp.sport), int(tcp.dport)
    elif udp is not None:
        protocol, src_port, dst_port = "udp", int(udp.sport), int(udp.dport)
    elif _layer(packet, "ICMP") is not None:
        protocol, src_port, dst_port = "icmp", 0, 0
    else:
        protocol, src_port, dst_port = "other", 0, 0

    timestamp = float(getattr(packet, "time", 0.0))
    return {
        "timestamp": timestamp,
        "size": float(len(packet)),
        "src": src,
        "dst": dst,
        "proto": int(proto) if proto is not None else -1,
        "protocol": protocol,
        "src_port": src_port,
        "dst_port": dst_port,
        "is_esp": int(_layer(packet, "ESP") is not None or proto == 50),
        "is_ike": int(bool(protocol == "udp" and ({src_port, dst_port} & {500, 4500}))),
    }


def _flow_key(record: Dict[str, Any]) -> Tuple[Any, ...]:
    left = (record["src"], record["src_port"])
    right = (record["dst"], record["dst_port"])
    endpoints = tuple(sorted((left, right), key=str))
    return (record["protocol"], *endpoints)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator > 0 else 0.0


def _iso_timestamp(timestamp: float) -> str:
    if timestamp <= 0:
        return "1970-01-01T00:00:00+00:00"
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def extract_behavioral_features(
    packets: Iterable[Any],
    *,
    window_start: Optional[float] = None,
    window_end: Optional[float] = None,
) -> Dict[str, Any]:
    """Aggregate one packet window into the versioned behavioral schema.

    Direction is defined per bidirectional 5-tuple by the first observed
    packet. This is a measurable transport-level convention, not an inference
    about which endpoint is trusted or compromised.
    """
    records = [_packet_record(packet) for packet in packets]
    if window_start is not None:
        records = [record for record in records if record["timestamp"] >= window_start]
    if window_end is not None:
        records = [record for record in records if record["timestamp"] < window_end]
    records.sort(key=lambda record: record["timestamp"])

    if not records:
        return {
            "timestamp": _iso_timestamp(window_start or 0),
            "duration_sec": 0.0,
            "packet_count": 0.0,
            "byte_count": 0.0,
            **{name: 0.0 for name in (
                "packets_per_second", "bytes_per_second", "mean_packet_size",
                "std_packet_size", "min_packet_size", "max_packet_size",
                "mean_inter_arrival_time", "std_inter_arrival_time",
                "forward_packet_count", "backward_packet_count", "forward_byte_count",
                "backward_byte_count", "flow_count", "new_flows_per_minute",
                "concurrent_flows", "unique_source_count", "unique_destination_count",
                "peer_count", "inbound_outbound_byte_ratio", "inbound_outbound_packet_ratio",
                "tcp_packet_count", "udp_packet_count", "icmp_packet_count",
                "other_packet_count", "esp_packet_count", "ike_packet_count",
                "sa_establishment_frequency", "session_duration_mean", "session_duration_std"
            )},
        }

    timestamps = np.asarray([record["timestamp"] for record in records], dtype=float)
    sizes = np.asarray([record["size"] for record in records], dtype=float)
    duration = max(0.0, float(timestamps[-1] - timestamps[0]))
    iats = np.diff(timestamps) if len(timestamps) > 1 else np.asarray([0.0])

    flow_first_direction: Dict[Tuple[Any, ...], Tuple[Optional[str], Optional[int]]] = {}
    flow_stats: Dict[Tuple[Any, ...], Dict[str, Any]] = defaultdict(
        lambda: {"first": None, "last": None, "packet_count": 0, "byte_count": 0.0}
    )
    forward_packets = backward_packets = 0
    forward_bytes = backward_bytes = 0.0
    active_events: List[Tuple[float, int]] = []
    sources, destinations, peers = set(), set(), set()

    for record in records:
        key = _flow_key(record)
        orientation = (record["src"], record["src_port"])
        if key not in flow_first_direction:
            flow_first_direction[key] = orientation
        is_forward = orientation == flow_first_direction[key]
        if is_forward:
            forward_packets += 1
            forward_bytes += record["size"]
        else:
            backward_packets += 1
            backward_bytes += record["size"]

        stats = flow_stats[key]
        stats["first"] = record["timestamp"] if stats["first"] is None else stats["first"]
        stats["last"] = record["timestamp"]
        stats["packet_count"] += 1
        stats["byte_count"] += record["size"]
        if record["src"]:
            sources.add(record["src"])
            peers.add(record["src"])
        if record["dst"]:
            destinations.add(record["dst"])
            peers.add(record["dst"])

    for stats in flow_stats.values():
        active_events.append((stats["first"], 1))
        active_events.append((stats["last"], -1))
    active_events.sort(key=lambda item: (item[0], item[1]))
    concurrent = current = 0
    for _, delta in active_events:
        current += delta
        concurrent = max(concurrent, current)

    flow_durations = np.asarray(
        [max(0.0, stats["last"] - stats["first"]) for stats in flow_stats.values()],
        dtype=float,
    )
    if len(flow_durations) == 0:
        flow_durations = np.asarray([0.0])
    protocol_counts = {name: sum(record["protocol"] == name for record in records) for name in ("tcp", "udp", "icmp", "other")}
    esp_count = sum(record["is_esp"] for record in records)
    ike_count = sum(record["is_ike"] for record in records)
    sa_frequency = _safe_ratio(ike_count, duration) if duration else float(ike_count)

    return {
        "timestamp": _iso_timestamp(timestamps[0]),
        "duration_sec": duration,
        "packet_count": float(len(records)),
        "byte_count": float(np.sum(sizes)),
        "packets_per_second": _safe_ratio(len(records), duration) if duration else float(len(records)),
        "bytes_per_second": _safe_ratio(float(np.sum(sizes)), duration) if duration else float(np.sum(sizes)),
        "mean_packet_size": float(np.mean(sizes)),
        "std_packet_size": float(np.std(sizes)),
        "min_packet_size": float(np.min(sizes)),
        "max_packet_size": float(np.max(sizes)),
        "mean_inter_arrival_time": float(np.mean(iats)),
        "std_inter_arrival_time": float(np.std(iats)),
        "forward_packet_count": float(forward_packets),
        "backward_packet_count": float(backward_packets),
        "forward_byte_count": float(forward_bytes),
        "backward_byte_count": float(backward_bytes),
        "flow_count": float(len(flow_stats)),
        "new_flows_per_minute": _safe_ratio(len(flow_stats), duration) * 60.0 if duration else float(len(flow_stats)),
        "concurrent_flows": float(concurrent),
        "unique_source_count": float(len(sources)),
        "unique_destination_count": float(len(destinations)),
        "peer_count": float(len(peers)),
        "inbound_outbound_byte_ratio": _safe_ratio(backward_bytes, forward_bytes),
        "inbound_outbound_packet_ratio": _safe_ratio(backward_packets, forward_packets),
        "tcp_packet_count": float(protocol_counts["tcp"]),
        "udp_packet_count": float(protocol_counts["udp"]),
        "icmp_packet_count": float(protocol_counts["icmp"]),
        "other_packet_count": float(protocol_counts["other"]),
        "esp_packet_count": float(esp_count),
        "ike_packet_count": float(ike_count),
        "sa_establishment_frequency": sa_frequency,
        "session_duration_mean": float(np.mean(flow_durations)),
        "session_duration_std": float(np.std(flow_durations)),
    }


def extract_pcap_windows(pcap_path: str, window_seconds: float = 60.0) -> List[Dict[str, Any]]:
    """Read a PCAP and return non-overlapping behavioral windows."""
    from scapy.utils import rdpcap

    packets = rdpcap(pcap_path)
    if not packets:
        return [extract_behavioral_features([])]
    timestamps = [float(getattr(packet, "time", 0.0)) for packet in packets]
    start = min(timestamps)
    end = max(timestamps)
    windows: List[Dict[str, Any]] = []
    current = start
    while current <= end or not windows:
        window = extract_behavioral_features(
            packets,
            window_start=current,
            window_end=current + window_seconds,
        )
        if window["packet_count"] > 0:
            windows.append(window)
        current += window_seconds
    return windows
