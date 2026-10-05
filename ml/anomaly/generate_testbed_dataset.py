"""Run the existing strongSwan testbed and build a real PCAP-derived dataset.

This command deliberately enables strict capture mode. If the orchestrator
cannot reach the VMs or retrieve the observer PCAP, it fails instead of using
the repository's sample-PCAP fallback.

Example:
    python -m ml.anomaly.generate_testbed_dataset --all --runs-per-scenario 3
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from db.repository import TestbedJobRepository
from ml.anomaly.feature_extractor import extract_pcap_windows
from ml.anomaly.schemas import FEATURE_COLUMNS
from services.testbed.models import TestbedState, TestbedTopology, VMHostConfig
from services.testbed.orchestrator import TestbedOrchestrator

SCENARIO_MAP: Dict[str, Dict[str, object]] = {
    "ikev2-aes-gcm-compliant": {"scenario_type": "normal", "label": 0},
    "ikev2-rekey-stress": {"scenario_type": "session_anomaly", "label": 1},
    "ikev2-dns-tunnel": {"scenario_type": "burst_pattern", "label": 1},
    "ikev2-p2p-tunnel": {"scenario_type": "traffic_spike", "label": 1},
    "multi-tunnel-hub-spoke-mesh": {"scenario_type": "flow_spike", "label": 1},
}


def _scenario_ids(all_scenarios: bool, requested: Iterable[str]) -> List[str]:
    if all_scenarios:
        return list(SCENARIO_MAP)
    selected = list(requested)
    unknown = sorted(set(selected) - set(SCENARIO_MAP))
    if unknown:
        raise ValueError(f"Unsupported dataset scenario ids: {unknown}")
    return selected


async def _run_scenario(scenario_id: str, topology: TestbedTopology) -> str:
    orchestrator = TestbedOrchestrator()
    scenario = orchestrator.get_scenario_by_id(scenario_id)
    if scenario is None:
        raise ValueError(f"strongSwan scenario not found: {scenario_id}")

    job = TestbedJobRepository.create_job(scenario.name, {
        "scenario": scenario.model_dump() if hasattr(scenario, "model_dump") else scenario.dict(),
        "topology": topology.model_dump() if hasattr(topology, "model_dump") else topology.dict(),
        "dataset_generation": True,
    })
    result = await orchestrator.execute_scenario(job["id"], scenario, topology)
    if result.state != TestbedState.COMPLETED:
        raise RuntimeError(f"strongSwan scenario {scenario_id} failed: {result.error_message}")

    completed = TestbedJobRepository.get_job(job["id"]) or {}
    pcap_path = completed.get("pcap_storage_path")
    if not pcap_path or not Path(pcap_path).is_file():
        raise FileNotFoundError(f"Completed testbed job did not produce a PCAP: {job['id']}")
    return pcap_path


async def _collect(
    scenario_ids: List[str], runs_per_scenario: int, window_seconds: float, topology: TestbedTopology
) -> pd.DataFrame:
    rows = []
    for scenario_id in scenario_ids:
        for run_index in range(runs_per_scenario):
            pcap_path = await _run_scenario(scenario_id, topology)
            info = SCENARIO_MAP[scenario_id]
            windows = extract_pcap_windows(pcap_path, window_seconds=window_seconds)
            for window_index, window in enumerate(windows):
                rows.append({
                    "sample_id": f"testbed-{scenario_id}-{run_index:03d}-{window_index:03d}",
                    "scenario_type": info["scenario_type"],
                    "label": info["label"],
                    "data_source": "strongswan_testbed_pcap",
                    "source_pcap": str(pcap_path),
                    **{column: window[column] for column in ["timestamp", *FEATURE_COLUMNS]},
                })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate behavioral dataset from real strongSwan testbed PCAPs")
    parser.add_argument("--scenario", action="append", choices=sorted(SCENARIO_MAP), default=[])
    parser.add_argument("--all", action="store_true", help="Run the default normal and controlled testbed scenarios")
    parser.add_argument("--runs-per-scenario", type=int, default=1)
    parser.add_argument("--window-seconds", type=float, default=60.0)
    parser.add_argument("--output", default="ml/anomaly/datasets/vpn_behavioral_testbed.csv")
    parser.add_argument("--initiator", default="192.168.56.10")
    parser.add_argument("--responder", default="192.168.57.20")
    parser.add_argument("--observer", default="192.168.56.1")
    parser.add_argument("--docker", action="store_true", help="Use localhost forwarded SSH ports for Docker testbed nodes")
    args = parser.parse_args()
    if not args.all and not args.scenario:
        parser.error("provide --all or at least one --scenario")
    if args.runs_per_scenario < 1:
        parser.error("--runs-per-scenario must be at least 1")

    scenario_ids = _scenario_ids(args.all, args.scenario)
    # This environment flag is consumed by CaptureManager and prevents the
    # normal offline sample fallback from contaminating the dataset.
    os.environ["TESTBED_REQUIRE_REAL_CAPTURE"] = "1"
    if args.docker:
        topology = TestbedTopology(
            initiator=VMHostConfig(host=args.initiator, port=2201, ssh_host="127.0.0.1", interface="eth0"),
            responder=VMHostConfig(host=args.responder, port=2202, ssh_host="127.0.0.1", interface="eth0"),
            # Docker mode places the observer inline between two network
            # segments, so its `any` interface sees the real forwarded IKE/ESP
            # exchange while it remains a separate container.
            observer=VMHostConfig(host=args.observer, port=2203, ssh_host="127.0.0.1", interface="any"),
        )
    else:
        topology = TestbedTopology(
            initiator={"host": args.initiator, "interface": "eth1"},
            responder={"host": args.responder, "interface": "eth1"},
            observer={"host": args.observer, "interface": "eth1"},
        )
    frame = asyncio.run(_collect(scenario_ids, args.runs_per_scenario, args.window_seconds, topology))
    if frame.empty:
        raise RuntimeError("strongSwan testbed completed but yielded no packet windows")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Wrote {len(frame)} real PCAP-derived windows to {output}")
    print(frame.groupby(["scenario_type", "label"]).size().to_string())


if __name__ == "__main__":
    main()
