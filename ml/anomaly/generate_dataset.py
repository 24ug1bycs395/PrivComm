"""Generate controlled behavioral windows or extract windows from a PCAP.

Examples:
    python -m ml.anomaly.generate_dataset --all --samples 1000
    python -m ml.anomaly.generate_dataset --scenario traffic_spike --samples 500
    python -m ml.anomaly.generate_dataset --pcap samples/example.pcapng
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from ml.anomaly.feature_extractor import extract_pcap_windows
from ml.anomaly.schemas import FEATURE_COLUMNS, SCENARIO_TYPES


SCENARIOS = [
    "normal",
    "traffic_spike",
    "flow_spike",
    "peer_activity_anomaly",
    "burst_pattern",
    "session_anomaly",
]


def _normal_record(rng: np.random.Generator) -> Dict[str, float]:
    duration = float(np.clip(rng.normal(60.0, 8.0), 20.0, 100.0))
    packet_rate = float(np.clip(rng.normal(18.0, 3.0), 5.0, 40.0))
    packet_count = max(1.0, round(packet_rate * duration))
    mean_size = float(np.clip(rng.normal(420.0, 70.0), 80.0, 900.0))
    byte_count = packet_count * mean_size
    flow_count = float(np.clip(round(rng.normal(8.0, 2.0)), 2.0, 18.0))
    return {
        "duration_sec": duration,
        "packet_count": packet_count,
        "byte_count": byte_count,
        "packets_per_second": packet_count / duration,
        "bytes_per_second": byte_count / duration,
        "mean_packet_size": mean_size,
        "std_packet_size": float(np.clip(rng.normal(95.0, 20.0), 10.0, 240.0)),
        "min_packet_size": float(np.clip(rng.normal(80.0, 15.0), 40.0, 150.0)),
        "max_packet_size": float(np.clip(rng.normal(1400.0, 80.0), 800.0, 1500.0)),
        "mean_inter_arrival_time": 1.0 / (packet_count / duration),
        "std_inter_arrival_time": float(np.clip(rng.normal(0.025, 0.008), 0.002, 0.08)),
        "forward_packet_count": packet_count * 0.58,
        "backward_packet_count": packet_count * 0.42,
        "forward_byte_count": byte_count * 0.62,
        "backward_byte_count": byte_count * 0.38,
        "flow_count": flow_count,
        "new_flows_per_minute": flow_count / duration * 60.0,
        "concurrent_flows": float(np.clip(rng.normal(4.0, 1.0), 1.0, 9.0)),
        "unique_source_count": 2.0,
        "unique_destination_count": 2.0,
        "peer_count": 2.0,
        "inbound_outbound_byte_ratio": 0.38 / 0.62,
        "inbound_outbound_packet_ratio": 0.42 / 0.58,
        "tcp_packet_count": packet_count * 0.55,
        "udp_packet_count": packet_count * 0.25,
        "icmp_packet_count": packet_count * 0.05,
        "other_packet_count": packet_count * 0.15,
        "esp_packet_count": packet_count * 0.82,
        "ike_packet_count": float(np.clip(rng.normal(2.0, 0.6), 0.0, 5.0)),
        "sa_establishment_frequency": 2.0 / duration,
        "session_duration_mean": duration / flow_count,
        "session_duration_std": duration / flow_count * 0.25,
    }


def _controlled_record(scenario: str, rng: np.random.Generator) -> Dict[str, float]:
    record = _normal_record(rng)
    if scenario == "traffic_spike":
        record["packets_per_second"] *= float(rng.uniform(2.5, 5.0))
        record["bytes_per_second"] *= float(rng.uniform(4.0, 10.0))
        record["packet_count"] = record["packets_per_second"] * record["duration_sec"]
        record["byte_count"] = record["bytes_per_second"] * record["duration_sec"]
    elif scenario == "flow_spike":
        record["flow_count"] *= float(rng.uniform(4.0, 8.0))
        record["new_flows_per_minute"] = record["flow_count"] / record["duration_sec"] * 60.0
        record["concurrent_flows"] *= float(rng.uniform(4.0, 8.0))
    elif scenario == "peer_activity_anomaly":
        peers = float(rng.integers(8, 30))
        record["peer_count"] = peers
        record["unique_source_count"] = float(rng.integers(4, 16))
        record["unique_destination_count"] = float(rng.integers(4, 16))
        record["flow_count"] *= float(rng.uniform(2.0, 5.0))
        record["new_flows_per_minute"] = record["flow_count"] / record["duration_sec"] * 60.0
    elif scenario == "burst_pattern":
        record["std_inter_arrival_time"] *= float(rng.uniform(8.0, 20.0))
        record["mean_inter_arrival_time"] *= float(rng.uniform(0.15, 0.45))
        record["packets_per_second"] *= float(rng.uniform(1.5, 3.0))
    elif scenario == "session_anomaly":
        record["flow_count"] *= float(rng.uniform(3.0, 7.0))
        record["new_flows_per_minute"] = record["flow_count"] / record["duration_sec"] * 60.0
        record["session_duration_mean"] *= float(rng.uniform(0.03, 0.2))
        record["session_duration_std"] *= float(rng.uniform(1.5, 4.0))
        record["sa_establishment_frequency"] *= float(rng.uniform(4.0, 12.0))
    return record


def generate_controlled_dataset(scenario: str, samples: int, seed: int = 42) -> pd.DataFrame:
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}")
    rng = np.random.default_rng(seed)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rows = []
    for index in range(samples):
        feature_values = _controlled_record(scenario, rng)
        rows.append({
            "sample_id": f"synthetic-{scenario}-{index:06d}",
            "timestamp": (start + timedelta(seconds=index * 60)).isoformat(),
            "scenario_type": scenario,
            "label": int(scenario != "normal"),
            "data_source": "synthetic_controlled",
            **{column: float(feature_values[column]) for column in FEATURE_COLUMNS},
        })
    return pd.DataFrame(rows)


def generate_pcap_dataset(pcap_path: str, window_seconds: float, label: int, scenario: str) -> pd.DataFrame:
    windows = extract_pcap_windows(pcap_path, window_seconds=window_seconds)
    rows = []
    for index, window in enumerate(windows):
        rows.append({
            "sample_id": f"pcap-{Path(pcap_path).stem}-{index:06d}",
            "scenario_type": scenario,
            "label": label,
            "data_source": "pcap",
            **window,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VPN behavioral anomaly records")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", choices=SCENARIOS)
    group.add_argument("--all", action="store_true", help="Generate all controlled scenarios")
    group.add_argument("--pcap", type=str, help="Extract real features from a PCAP/PCAPNG")
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--window-seconds", type=float, default=60.0)
    parser.add_argument("--pcap-label", type=int, choices=[0, 1], default=0)
    parser.add_argument("--pcap-scenario", default="pcap_observation")
    parser.add_argument("--output", default="ml/anomaly/datasets/vpn_behavioral_dataset.csv")
    args = parser.parse_args()

    if args.pcap:
        frame = generate_pcap_dataset(args.pcap, args.window_seconds, args.pcap_label, args.pcap_scenario)
    else:
        scenarios = SCENARIOS if args.all else [args.scenario]
        frame = pd.concat(
            [generate_controlled_dataset(scenario, args.samples, args.seed + index) for index, scenario in enumerate(scenarios)],
            ignore_index=True,
        )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Wrote {len(frame)} records to {output}")
    print(frame.groupby(["scenario_type", "label"]).size().to_string())


if __name__ == "__main__":
    main()
