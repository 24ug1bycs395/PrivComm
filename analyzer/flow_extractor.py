import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "duration", "total_fiat", "total_biat", "min_fiat", "min_biat",
    "max_fiat", "max_biat", "mean_fiat", "mean_biat", "flowPktsPerSecond",
    "flowBytesPerSecond", "min_flowiat", "max_flowiat", "mean_flowiat",
    "std_flowiat", "min_active", "mean_active", "max_active", "std_active",
    "min_idle", "mean_idle", "max_idle", "std_idle", "bytes_per_pkt",
    "fiat_biat_ratio", "log_duration", "log_bytes_sec", "log_pkts_sec"
]

def extract_flow_features_scapy(packets: List[Any]) -> Dict[str, float]:
    """Extract network flow features from Scapy packet sequence."""
    if not packets:
        return {}

    timestamps = []
    sizes = []
    directions = [] # True for forward, False for backward

    first_src = None

    from scapy.all import IP, IPv6

    for pkt in packets:
        t = float(getattr(pkt, "time", 0.0))
        timestamps.append(t)
        sz = len(pkt)
        sizes.append(sz)

        # Determine source address — supports both IPv4 and IPv6
        if pkt.haslayer(IP):
            src = pkt[IP].src
            if first_src is None:
                first_src = src
            directions.append(src == first_src)
        elif pkt.haslayer(IPv6):
            src = pkt[IPv6].src
            if first_src is None:
                first_src = src
            directions.append(src == first_src)
        else:
            directions.append(True)


    if not timestamps:
        return {}

    # Sort packets chronologically if out of order
    sorted_pairs = sorted(zip(timestamps, sizes, directions, strict=False), key=lambda x: x[0])
    timestamps = [p[0] for p in sorted_pairs]
    sizes = [p[1] for p in sorted_pairs]
    directions = [p[2] for p in sorted_pairs]

    total_pkts = len(timestamps)
    total_bytes = sum(sizes)

    # Convert timestamps to microseconds to align with flow dataset metrics
    start_t = timestamps[0]
    end_t = timestamps[-1]
    duration_sec = end_t - start_t
    duration_us = duration_sec * 1e6

    # Packet inter-arrival times overall
    flow_iats = np.diff(timestamps) * 1e6 if total_pkts > 1 else np.array([0.0])

    # Forward vs Backward IATs
    f_ts = [timestamps[i] for i in range(total_pkts) if directions[i]]
    b_ts = [timestamps[i] for i in range(total_pkts) if not directions[i]]

    f_iats = np.diff(f_ts) * 1e6 if len(f_ts) > 1 else np.array([0.0])
    b_iats = np.diff(b_ts) * 1e6 if len(b_ts) > 1 else np.array([0.0])

    pkts_per_sec = float(total_pkts / duration_sec) if duration_sec > 0 else float(total_pkts)
    bytes_per_sec = float(total_bytes / duration_sec) if duration_sec > 0 else float(total_bytes)

    features = {
        "duration": float(duration_us),
        "total_fiat": float(np.sum(f_iats)),
        "total_biat": float(np.sum(b_iats)),
        "min_fiat": float(np.min(f_iats)),
        "min_biat": float(np.min(b_iats)),
        "max_fiat": float(np.max(f_iats)),
        "max_biat": float(np.max(b_iats)),
        "mean_fiat": float(np.mean(f_iats)),
        "mean_biat": float(np.mean(b_iats)),
        "flowPktsPerSecond": pkts_per_sec,
        "flowBytesPerSecond": bytes_per_sec,
        "min_flowiat": float(np.min(flow_iats)),
        "max_flowiat": float(np.max(flow_iats)),
        "mean_flowiat": float(np.mean(flow_iats)),
        "std_flowiat": float(np.std(flow_iats)),
        "min_active": -1.0,
        "mean_active": 0.0,
        "max_active": -1.0,
        "std_active": 0.0,
        "min_idle": -1.0,
        "mean_idle": 0.0,
        "max_idle": float(np.max(flow_iats)),
        "std_idle": 0.0,
    }

    # Engineered features
    bytes_per_pkt = total_bytes / (total_pkts + 1e-5)
    fiat_biat_ratio = features["mean_fiat"] / (features["mean_biat"] + 1e-5)
    log_duration = float(np.log1p(max(0.0, duration_us)))
    log_bytes_sec = float(np.log1p(max(0.0, bytes_per_sec)))
    log_pkts_sec = float(np.log1p(max(0.0, pkts_per_sec)))

    features["bytes_per_pkt"] = bytes_per_pkt
    features["fiat_biat_ratio"] = fiat_biat_ratio
    features["log_duration"] = log_duration
    features["log_bytes_sec"] = log_bytes_sec
    features["log_pkts_sec"] = log_pkts_sec

    return features
