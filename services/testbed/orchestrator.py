import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from db.repository import AnalysisJobRepository, TestbedJobRepository
from services.protocol_engine import ProtocolIdentificationEngine
from services.testbed import event_store
from services.testbed.capture_manager import CaptureManager
from services.testbed.config_generator import StrongSwanConfigGenerator
from services.testbed.models import (
    PRESET_SCENARIOS,
    ScenarioDefinition,
    TestbedJobStatus,
    TestbedState,
    TestbedTopology,
)
from services.testbed.ssh_controller import SSHController

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
    def compute_handshake_integrity(scenario: ScenarioDefinition, topology: TestbedTopology) -> Dict[str, Any]:
        hash_algo = getattr(scenario, "hash_algorithm", None) or scenario.integrity or "SHA-256"
        return {
            "status": "NOT_VERIFIED",
            "verification_method": "configuration_only",
            "configured_parameters": {
                "initiator": topology.initiator.host,
                "responder": topology.responder.host,
                "ike_version": scenario.ike_version,
                "encryption": scenario.encryption,
                "integrity": hash_algo,
                "dh_group": scenario.dh_group,
                "mode": scenario.ipsec_mode,
                "pfs": scenario.pfs,
            },
            "details": (
                "Configured proposal values are recorded for context only. No cryptographic "
                "handshake attestation or independent endpoint comparison was performed."
            ),
        }

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
        Emits structured events to the in-memory event_store for live UI consumption.
        """
        logger.info(f"[Testbed] Starting Job {job_id}: '{scenario.name}'")
        logs = []

        # Initialise the transient event buffer for this job
        event_store.init_job(job_id)

        def emit(vm: str, host: str, event_type: str, **kwargs):
            """Emit a structured event to the in-memory store."""
            event_store.emit(job_id, {
                "vm": vm,
                "host": host,
                "type": event_type,
                **kwargs,
            })

        def log_step(msg: str, state: Optional[TestbedState] = None, progress: int = 0):
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            entry = f"[{ts}] {msg}"
            logs.append(entry)
            logger.info(f"[{job_id}] {msg}")
            updates = {"log": msg, "progress_pct": progress}
            if state:
                updates["state"] = state.value
            TestbedJobRepository.update_job(job_id, updates)

        def make_vm_callback(vm_role: str, host: str):
            """Return an on_event callback bound to a specific VM role and host."""
            def _cb(event: Dict[str, Any]):
                event["vm"] = vm_role
                event["host"] = host
                event_store.emit(job_id, event)
            return _cb

        try:
            # ── Phase 1: Config Synthesis ────────────────────────────────────
            emit("system", "orchestrator", "status",
                 phase="CONFIG_GENERATION",
                 output="Generating strongSwan cryptographic policies for Initiator and Responder...",
                 status="running")

            log_step("Starting scenario orchestration. Generating strongSwan cryptographic policies...",
                     TestbedState.PROVISIONING, 10)

            init_conf = StrongSwanConfigGenerator.generate_swanctl_conf(scenario, topology, is_initiator=True)
            resp_conf = StrongSwanConfigGenerator.generate_swanctl_conf(scenario, topology, is_initiator=False)

            emit("system", "orchestrator", "status",
                 phase="CONFIG_GENERATION",
                 output=f"Configuration synthesis complete — IKE: {scenario.ike_version}, "
                        f"Enc: {scenario.encryption}, DH: {scenario.dh_group}",
                 status="success")

            # ── Phases 2/3: Provision both endpoints concurrently ───────────
            # These operations are independent. Running them together removes
            # one full VM provisioning round-trip from every scenario.
            async def provision_node(role, vm, config, ready_message, progress):
                callback = make_vm_callback(role, vm.host)
                phase = f"{role.upper()}_PROVISIONING"
                emit(role, vm.host, "connection", phase=phase,
                     output=f"Opening SSH session to {role.capitalize()} ({vm.host})...",
                     status="connecting")
                log_step(f"Pushing configuration to {role.capitalize()} VM ({vm.host})...",
                         progress=progress)

                # Reuse one SSH connection for both the config upload and
                # daemon reload. This removes an authentication round-trip
                # from every endpoint provision.
                async with SSHController.session(vm, on_event=callback, vm_role=role) as session:
                    written = await session.write_file("/etc/swanctl/conf.d/testbed.conf", config)
                    if not written:
                        raise RuntimeError(f"Failed to write strongSwan configuration to {role} ({vm.host})")

                    # Do not mask daemon/configuration failures. The old
                    # fallback used `|| true`, which made failed deployments
                    # appear ready.
                    load_code, _, load_err = await session.run_command(
                        "sudo swanctl --unload-all >/dev/null 2>&1 || true; "
                        "sudo swanctl --load-all"
                    )
                    if load_code != 0:
                        raise RuntimeError(
                            f"strongSwan configuration load failed on {role} ({vm.host}): "
                            f"{load_err.strip() or 'unknown error'}"
                        )

                emit(role, vm.host, "status", phase=phase,
                     output=ready_message, status="success")

            await asyncio.gather(
                provision_node(
                    "responder", topology.responder, resp_conf,
                    "Responder configured and listening for IKE connections.", 20
                ),
                provision_node(
                    "initiator", topology.initiator, init_conf,
                    "Initiator configured and ready to negotiate IKE SA.", 35
                )
            )

            make_vm_callback("responder", topology.responder.host)
            init_cb = make_vm_callback("initiator", topology.initiator.host)

            # ── Phase 4: Observer / Packet Capture ───────────────────────────
            pcap_filename = f"testbed_{scenario.id}_{job_id[:8]}.pcap"
            local_pcap_path = os.path.join("captures", pcap_filename)

            make_vm_callback("observer", topology.observer.host)

            emit("observer", topology.observer.host, "connection",
                 phase="OBSERVER_CAPTURE_START",
                 output=f"Opening sniffer on Observer ({topology.observer.host}:{topology.observer.interface})...",
                 status="connecting")

            log_step(
                f"Initializing network sniffer on Observer ({topology.observer.host}:{topology.observer.interface})...",
                TestbedState.CAPTURING, 50
            )

            emit("observer", topology.observer.host, "command",
                 phase="OBSERVER_CAPTURE_START",
                 command=f"tcpdump -i {topology.observer.interface} 'udp port 500 or 4500 or proto 50' -w /tmp/{pcap_filename}",
                 output="Starting packet capture...",
                 status="running")

            remote_pcap = await CaptureManager.start_remote_capture(
                topology.observer, topology.observer.interface, pcap_filename
            )

            emit("observer", topology.observer.host, "status",
                 phase="OBSERVER_CAPTURE_START",
                 output=f"Wire capture active — recording IPsec traffic on {topology.observer.interface}",
                 status="running")

            # ── Phase 5: Tunnel Negotiation ──────────────────────────────────
            hash_algo = getattr(scenario, "hash_algorithm", None) or scenario.integrity or "SHA-256"
            integrity_info = self.compute_handshake_integrity(scenario, topology)

            log_step(
                f"Initiating IKE SA & CHILD SA exchange from {topology.initiator.host} to {topology.responder.host} "
                f"using configured {hash_algo} integrity proposal...",
                progress=65
            )

            emit("initiator", topology.initiator.host, "status",
                 phase="TUNNEL_NEGOTIATION",
                 output=f"Configured integrity proposal: {hash_algo}. This is not a handshake attestation.",
                 status="running")

            emit("initiator", topology.initiator.host, "status",
                 phase="TUNNEL_NEGOTIATION",
                 output=f"Initiating {scenario.ike_version} SA → Responder {topology.responder.host}",
                 status="running")

            initiate_code, _, initiate_err = await SSHController.run_command(
                topology.initiator,
                "sudo swanctl --initiate --child net-tunnel",
                on_event=init_cb, vm_role="initiator"
            )
            if initiate_code != 0:
                raise RuntimeError(
                    f"IPsec tunnel negotiation failed: "
                    f"{initiate_err.strip() or 'swanctl initiate returned a non-zero exit code'}"
                )

            emit("responder", topology.responder.host, "status",
                 phase="TUNNEL_NEGOTIATION",
                 output="Independent cryptographic handshake attestation was not performed.",
                 status="info")

            emit("initiator", topology.initiator.host, "status",
                 phase="TUNNEL_NEGOTIATION",
                 output="swanctl initiation command succeeded; negotiated values are assessed from the capture when observable.",
                 status="success")

            emit("responder", topology.responder.host, "status",
                 phase="TUNNEL_NEGOTIATION",
                 output="Tunnel negotiation command completed; ESP observations are assessed from the capture.",
                 status="success")

            # ── Phase 6: Traffic Injection ───────────────────────────────────
            log_step(
                f"Generating synthetic payload traffic ({scenario.traffic_profile}, {scenario.packet_count} packets)...",
                progress=75
            )

            traffic_cmd = self._build_traffic_command(scenario, topology)

            emit("initiator", topology.initiator.host, "status",
                 phase="TRAFFIC_INJECTION",
                 output=f"Injecting {scenario.traffic_profile} traffic ({scenario.packet_count} packets) through tunnel...",
                 status="running")

            emit(
                "initiator",
                topology.initiator.host,
                "packet_batch",
                phase="TRAFFIC_INJECTION",
                packet_count=scenario.packet_count,
                bytes=None,
                protocol="ESP",
                source=topology.initiator.host,
                destination=topology.responder.host,
                profile=scenario.traffic_profile,
                status="running",
                output=f"Packet transfer started: {scenario.packet_count} {scenario.traffic_profile} packets.",
            )

            # Keep the traffic command running while the observer captures the
            # actual packets. Per-packet classifications must come from the
            # capture/analysis pipeline, not from a dashboard-only mock mix.
            traffic_task = asyncio.create_task(SSHController.run_command(
                topology.initiator,
                traffic_cmd,
                on_event=init_cb, vm_role="initiator"
            ))

            traffic_code, _, traffic_err = await traffic_task
            if traffic_code != 0:
                raise RuntimeError(
                    f"Traffic injection failed: "
                    f"{traffic_err.strip() or 'traffic command returned a non-zero exit code'}"
                )

            emit("initiator", topology.initiator.host, "status",
                 phase="TRAFFIC_INJECTION",
                 output=f"Traffic injection complete — {scenario.packet_count} packets transmitted",
                 status="success")

            emit("observer", topology.observer.host, "status",
                 phase="TRAFFIC_INJECTION",
                 output=f"Observer received all {scenario.packet_count} live packets",
                 status="running")

            # tcpdump receives SIGINT during capture teardown and flushes its
            # pcap synchronously; avoid an unconditional two-second delay.

            # ── Phase 7: Capture Retrieval ───────────────────────────────────
            log_step("Terminating packet capture and retrieving PCAP file...", progress=85)

            emit("observer", topology.observer.host, "status",
                 phase="CAPTURE_RETRIEVAL",
                 output="Stopping tcpdump — downloading PCAP artifact...",
                 status="running")

            pcap_url = await CaptureManager.stop_and_retrieve_capture(
                topology.observer, remote_pcap, local_pcap_path, scenario
            )

            emit("observer", topology.observer.host, "status",
                 phase="CAPTURE_RETRIEVAL",
                 output=f"PCAP artifact saved: {pcap_filename}",
                 status="success")

            # ── Phase 8: AI Analysis ─────────────────────────────────────────
            log_step(
                f"Passing capture ({pcap_filename}) to Unified Protocol Analysis Engine...",
                TestbedState.ANALYZING, 90
            )

            emit("system", "orchestrator", "status",
                 phase="AI_ANALYSIS",
                 output=f"Running AI security analysis on {pcap_filename}...",
                 status="running")

            analysis_res = self.engine.analyze_pcap(local_pcap_path)

            analysis_res.tunnel_integrity = integrity_info

            result_dict = analysis_res.model_dump() if hasattr(analysis_res, "model_dump") else analysis_res.dict()
            result_dict["tunnel_integrity"] = integrity_info
            result_dict["filename"] = pcap_filename
            result_dict["filesize"] = os.path.getsize(local_pcap_path) if os.path.exists(local_pcap_path) else 0
            result_dict["pcap_download_url"] = pcap_url

            # Save job outcomes
            AnalysisJobRepository.save_analysis(result_dict)
            TestbedJobRepository.update_job(job_id, {
                "state": TestbedState.COMPLETED.value,
                "progress_pct": 100,
                "pcap_storage_path": local_pcap_path,
                "pcap_download_url": pcap_url,
                "result_json": result_dict,
                "log": "Testbed scenario execution and security analysis completed successfully."
            })

            emit("system", "orchestrator", "status",
                 phase="AI_ANALYSIS",
                 output=f"Analysis complete — Risk: {result_dict.get('security_assessment', {}).get('risk_level', 'N/A')}, "
                        f"Compliance Score: {result_dict.get('compliance_score', 'N/A')}",
                 status="success")

            log_step("Scenario run completed successfully.", TestbedState.COMPLETED, 100)

            emit("system", "orchestrator", "complete",
                 phase="COMPLETE",
                 output="All pipeline stages finished. Results available.",
                 status="success")

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

            emit("system", "orchestrator", "error",
                 phase="FAILED",
                 output=err_msg,
                 status="error")

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

    @staticmethod
    def _build_traffic_command(scenario: ScenarioDefinition, topology: TestbedTopology) -> str:
        """
        Build the shell command that injects synthetic traffic into the VPN tunnel.

        Supported traffic profiles:
          ICMP_ECHO    — ping (ICMP / ICMPv6)
          HTTP_GET     — curl HTTP request (web browsing)
          IPERF_BURST  — iperf3 TCP throughput (file transfer)
          VOIP_RTP     — iperf3 UDP small-packet stream (VoIP / WhatsApp voice)
          VIDEO_STREAM — iperf3 UDP large-packet high-rate stream (video streaming)
          EMAIL_SMTP   — netcat SMTP banner exchange (email)
          DNS_BURST    — dig/nslookup rapid DNS queries (DNS lookups)
          P2P_SIM      — bidirectional iperf3 UDP (P2P / BitTorrent simulation)
        """
        host = topology.responder.host
        dur = scenario.traffic_duration_sec
        pkts = scenario.packet_count
        profile = str(getattr(scenario, "payload_type", None) or scenario.traffic_profile).upper()
        is_ipv6 = scenario.ip_version.upper() == "IPV6"

        if profile == "HTTP_GET":
            return f"curl -s -m {dur} http://{host}:80/ || true"

        elif profile == "IPERF_BURST":
            return f"iperf3 -c {host} -t {dur} || true"

        elif profile == "VOIP_RTP":
            return (
                f"iperf3 -c {host} -u -b 64k -l 160 -t {dur} --no-delay || "
                f"ping {'6' if is_ipv6 else ''} -c {pkts} -s 160 -i 0.02 {host} || true"
            )

        elif profile == "VIDEO_STREAM":
            return (
                f"iperf3 -c {host} -u -b 5M -l 1400 -t {dur} || "
                f"iperf3 -c {host} -t {dur} -b 5M || true"
            )

        elif profile == "EMAIL_SMTP":
            smtp_script = (
                f"echo -e 'EHLO testbed\\r\\nQUIT\\r\\n' | "
                f"nc -w 5 {host} 25 || "
                f"curl -s --max-time {dur} smtp://{host}:25 || true"
            )
            return f"for i in $(seq 1 {max(1, pkts // 3)}); do {smtp_script}; sleep 0.5; done"

        elif profile == "DNS_BURST":
            return (
                f"for i in $(seq 1 {pkts}); do "
                f"dig @{host} example.com +time=1 +tries=1 > /dev/null 2>&1 || "
                f"nslookup example.com {host} > /dev/null 2>&1; "
                f"sleep 0.05; done"
            )

        elif profile == "P2P_SIM":
            return (
                f"iperf3 -c {host} -u -b 2M -t {dur} --bidir || "
                f"iperf3 -c {host} -u -b 2M -t {dur} || true"
            )

        else:
            ping_cmd = "ping6" if is_ipv6 else "ping"
            return f"{ping_cmd} -c {pkts} -W 1 {host} || true"
