"""Feature schema and validation for VPN behavioral anomaly records."""

from __future__ import annotations

from typing import Iterable, List

import numpy as np
import pandas as pd

SCHEMA_VERSION = "vpn-behavior-v1"

# These are all measurable from packet timestamps, IP endpoints, transport
# headers, and observable IKE/ESP protocol markers. No decrypted payload data
# or attack-specific labels are required.
FEATURE_COLUMNS: List[str] = [
    "duration_sec",
    "packet_count",
    "byte_count",
    "packets_per_second",
    "bytes_per_second",
    "mean_packet_size",
    "std_packet_size",
    "min_packet_size",
    "max_packet_size",
    "mean_inter_arrival_time",
    "std_inter_arrival_time",
    "forward_packet_count",
    "backward_packet_count",
    "forward_byte_count",
    "backward_byte_count",
    "flow_count",
    "new_flows_per_minute",
    "concurrent_flows",
    "unique_source_count",
    "unique_destination_count",
    "peer_count",
    "inbound_outbound_byte_ratio",
    "inbound_outbound_packet_ratio",
    "tcp_packet_count",
    "udp_packet_count",
    "icmp_packet_count",
    "other_packet_count",
    "esp_packet_count",
    "ike_packet_count",
    "sa_establishment_frequency",
    "session_duration_mean",
    "session_duration_std",
]

REQUIRED_COLUMNS = ["sample_id", "timestamp", "scenario_type", "label", *FEATURE_COLUMNS]
SCENARIO_TYPES = {
    "normal",
    "traffic_spike",
    "flow_spike",
    "peer_activity_anomaly",
    "burst_pattern",
    "session_anomaly",
    "pcap_observation",
}


def validate_dataframe(
    frame: pd.DataFrame,
    *,
    require_labels: bool = True,
    allowed_scenarios: Iterable[str] = SCENARIO_TYPES,
) -> pd.DataFrame:
    """Validate and return a normalized copy of a behavioral feature frame."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if not require_labels:
        missing = [column for column in missing if column not in {"label", "scenario_type"}]
    if missing:
        raise ValueError(f"Behavioral dataset is missing required columns: {missing}")

    result = frame.copy()
    if "label" in result:
        result["label"] = pd.to_numeric(result["label"], errors="raise").astype(int)
        invalid_labels = sorted(set(result["label"]) - {0, 1})
        if invalid_labels:
            raise ValueError(f"label must contain only 0 or 1; found {invalid_labels}")

    if "scenario_type" in result:
        unknown = sorted(set(result["scenario_type"].astype(str)) - set(allowed_scenarios))
        if unknown:
            raise ValueError(f"Unknown scenario_type values: {unknown}")

    for column in FEATURE_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="raise")
    values = result[FEATURE_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Behavioral features must not contain NaN or infinite values")
    if (result[FEATURE_COLUMNS] < 0).any().any():
        negative = result[FEATURE_COLUMNS].columns[(result[FEATURE_COLUMNS] < 0).any()].tolist()
        raise ValueError(f"Count/rate features cannot be negative: {negative}")

    if result.empty:
        raise ValueError("Behavioral dataset is empty")
    return result


def feature_matrix(frame: pd.DataFrame) -> np.ndarray:
    """Return the ordered numeric matrix consumed by the detector."""
    return frame[FEATURE_COLUMNS].to_numpy(dtype=float)
