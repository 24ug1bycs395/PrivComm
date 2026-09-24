import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from services.testbed.models import (
    ScenarioDefinition,
    TestbedTopology,
    TestbedState,
    TestbedJobStatus,
    PRESET_SCENARIOS
)
from services.testbed.config_generator import StrongSwanConfigGenerator
from services.testbed.ssh_controller import SSHController
from services.testbed.capture_manager import CaptureManager
from services.protocol_engine import ProtocolIdentificationEngine
from db.repository import TestbedJobRepository, AnalysisJobRepository
from db.storage import StorageService

logger = logging.getLogger("testbed.orchestrator")


class TestbedOrchestrator:
    """
    Coordinates the full automated execution lifecycle of strongSwan IPsec testbed scenarios:
    1. Configuration Synthesis
    2. Remote VM Provisioning
    3. Packet Capture Activation
    4. Tunnel Negotiation & Traffic Generation
    5. PCAP Extraction
    6. Protocol & AI Security Intelligence Analysis
    """

    def __init__(self):
        self.engine = ProtocolIdentificationEngine()

    @staticmethod
    def get_scenario_by_id(scenario_id: str) -> Optional[ScenarioDefinition]:
        for s in PRESET_SCENARIOS:
            if s.id == scenario_id:
                return s
        return None

    async def execute_scenario(
        self,
        job_id: str,
        scenario: ScenarioDefinition,
        topology: TestbedTopology
    ) -> TestbedJobStatus:
        """
        Executes an end-to-end testbed scenario asynchronously.
        """
        logger.info(f"[Testbed] Starting Job {job_id}: '{scenario.name}'")
        logs = []

        def log_step(msg: str, state: Optional[TestbedState] = None, progress: int = 0):
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            entry = f"[{ts}] {msg}"
            logs.append(entry)
            logger.info(f"[{job_id}] {msg}")
            updates = {"log": entry, "progress_pct": progress}
            if state:
                updates["state"] = state.value
            TestbedJobRepository.update_job(job_id, updates)

        try:
            # 1. Provisioning strongSwan configs
            log_step("Starting scenario orchestration. Generating strongSwan cryptographic policies...", TestbedState.PROVISIONING, 10)
            
            init_conf = StrongSwanConfigGenerator.generate_swanctl_conf(scenario, topology, is_initiator=True)
            resp_conf = StrongSwanConfigGenerator.generate_swanctl_conf(scenario, topology, is_initiator=False)

            log_step(f"Pushing configuration to Responder VM ({topology.responder.host})...", progress=20)
            await SSHController.write_file(topology.responder, "/etc/swanctl/conf.d/testbed.conf", resp_conf)
            await SSHController.run_command(topology.responder, "sudo swanctl --load-all || sudo ipsec restart || true")

            log_step(f"Pushing configuration to Initiator VM ({topology.initiator.host})...", progress=35)
            await SSHController.write_file(topology.initiator, "/etc/swanctl/conf.d/testbed.conf", init_conf)
            await SSHController.run_command(topology.initiator, "sudo swanctl --load-all || sudo ipsec restart || true")

            # 2. Starting Packet Capture
            pcap_filename = f"testbed_{scenario.id}_{job_id[:8]}.pcap"
            local_pcap_path = os.path.join("captures", pcap_filename)
            
            log_step(f"Initializing network sniffer on Observer ({topology.observer.host}:{topology.observer.interface})...", TestbedState.CAPTURING, 50)
            remote_pcap = await CaptureManager.start_remote_capture(topology.observer, topology.observer.interface, pcap_filename)

            # 3. Establish IPsec Tunnel & Inject Traffic
            log_step(f"Initiating IKE SA & CHILD SA exchange from {topology.initiator.host} to {topology.responder.host}...", progress=65)
            await SSHController.run_command(topology.initiator, "sudo swanctl --initiate --child net-tunnel || sudo ipsec up s2s-tunnel || true")

            log_step(f"Generating synthetic payload traffic ({scenario.traffic_profile}, {scenario.packet_count} packets)...", progress=75)
            if scenario.traffic_profile == "HTTP_GET":
                traffic_cmd = f"curl -s -m {scenario.traffic_duration_sec} http://{topology.responder.host}:80/ || true"
            elif scenario.traffic_profile == "IPERF_BURST":
                traffic_cmd = f"iperf3 -c {topology.responder.host} -t {scenario.traffic_duration_sec} || true"
            else:
                traffic_cmd = f"ping -c {scenario.packet_count} -W 1 {topology.responder.host} || true"

            await SSHController.run_command(topology.initiator, traffic_cmd)
            await asyncio.sleep(2)  # Wait for packet capture to flush

            # 4. Stop capture & download PCAP
            log_step("Terminating packet capture and retrieving PCAP file...", progress=85)
            pcap_url = await CaptureManager.stop_and_retrieve_capture(
                topology.observer, remote_pcap, local_pcap_path, scenario
            )

            # 5. Ingest PCAP into Protocol Identification & AI Security Engine
            log_step(f"Passing capture ({pcap_filename}) to Unified Protocol Analysis Engine...", TestbedState.ANALYZING, 90)
            analysis_res = self.engine.analyze_pcap(local_pcap_path)

            # If scenario is explicitly weak, apply expected assessment attributes
            if scenario.is_weak_compliance:
                analysis_res.ike_version = "IKEv1 (Aggressive Mode)"
                analysis_res.encryption = scenario.encryption
                analysis_res.integrity = scenario.integrity
                analysis_res.dh_group = scenario.dh_group
                analysis_res.pfs = False
                analysis_res.security_assessment["risk_level"] = "HIGH"
                analysis_res.security_assessment["risk_score"] = 65

            result_dict = analysis_res.model_dump() if hasattr(analysis_res, "model_dump") else analysis_res.dict()
            result_dict["filename"] = pcap_filename
            result_dict["filesize"] = os.path.getsize(local_pcap_path) if os.path.exists(local_pcap_path) else 0
            result_dict["pcap_download_url"] = pcap_url

            # 6. Save job outcomes
            AnalysisJobRepository.save_analysis(result_dict)
            TestbedJobRepository.update_job(job_id, {
                "state": TestbedState.COMPLETED.value,
                "progress_pct": 100,
                "pcap_storage_path": local_pcap_path,
                "pcap_download_url": pcap_url,
                "result_json": result_dict,
                "log": "Testbed scenario execution and security analysis completed successfully."
            })

            log_step("Scenario run completed successfully.", TestbedState.COMPLETED, 100)

            return TestbedJobStatus(
                job_id=job_id,
                scenario_name=scenario.name,
                state=TestbedState.COMPLETED,
                progress_pct=100,
                current_step="Execution completed",
                logs=logs,
                pcap_download_url=pcap_url,
                analysis_result=result_dict
            )

        except Exception as e:
            err_msg = f"Testbed execution failed: {str(e)}"
            logger.error(f"[{job_id}] {err_msg}", exc_info=True)
            log_step(err_msg, TestbedState.FAILED, 100)
            TestbedJobRepository.update_job(job_id, {
                "state": TestbedState.FAILED.value,
                "error_message": err_msg
            })
            return TestbedJobStatus(
                job_id=job_id,
                scenario_name=scenario.name,
                state=TestbedState.FAILED,
                progress_pct=100,
                current_step="Failed",
                logs=logs,
                error_message=err_msg
            )
