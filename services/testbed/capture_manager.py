import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from services.testbed.models import VMHostConfig, ScenarioDefinition
from services.testbed.ssh_controller import SSHController
from db.storage import StorageService

logger = logging.getLogger("testbed.capture_manager")

class CaptureManager:
    """
    Controls remote and local packet capture mechanisms for the testbed.
    """

    PROFILE_SAMPLE_MAP = {
        "HTTP_GET": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "IPERF_BURST": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_chacha20.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "VOIP_RTP": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_chacha20.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "VIDEO_STREAM": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_aes_gcm_2.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "EMAIL_SMTP": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_sha256.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "DNS_BURST": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_sha1.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "ICMP_ECHO": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "P2P_SIM": {
            "tunnel": "samples/ikev2_s2s_ipsec_vpn_chacha20_2.pcapng",
            "transport": "samples/ikev2_vpn.pcapng",
        },
        "DEFAULT": "samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng",
    }

    @staticmethod
    async def start_remote_capture(
        observer_vm: VMHostConfig,
        interface: str,
        pcap_filename: str
    ) -> str:
        """
        Starts tcpdump / tshark in background on the observer VM.
        Returns the remote capture file path.
        """
        remote_pcap = f"/tmp/{pcap_filename}"
        # Filter for ISAKMP (500), IPsec NAT-T (4500), and ESP (protocol 50)
        capture_cmd = (
            f"nohup sudo tcpdump -i {interface} 'udp port 500 or udp port 4500 or ip proto 50' "
            f"-w {remote_pcap} > /dev/null 2>&1 & echo $!"
        )
        code, stdout, stderr = await SSHController.run_command(observer_vm, capture_cmd)
        if code != 0:
            raise RuntimeError(
                f"Unable to start packet capture on {observer_vm.host}: "
                f"{stderr.strip() or 'tcpdump command failed'}"
            )
        logger.info(f"[CaptureManager] Started remote capture on {observer_vm.host}:{interface} -> {remote_pcap}")
        return remote_pcap

    @staticmethod
    async def stop_and_retrieve_capture(
        observer_vm: VMHostConfig,
        remote_pcap_path: str,
        local_pcap_path: str,
        scenario: ScenarioDefinition
    ) -> str:
        """
        Stops the remote capture, downloads the PCAP file, and uploads to StorageService.
        If running in simulated/offline mode, produces an appropriate scenario PCAP from samples.
        """
        # Stop tcpdump on observer
        # SIGINT lets tcpdump finish its pcap footer before the SFTP download.
        # The bracket expression prevents pkill from matching its own command.
        stop_cmd = "sudo pkill -INT -f '[t]cpdump' || true; sync"
        await SSHController.run_command(observer_vm, stop_cmd)

        os.makedirs(os.path.dirname(local_pcap_path), exist_ok=True)

        # Dataset generation can require an actual observer capture. In that
        # mode, never silently replace an unavailable capture with a sample.
        if not observer_vm.is_simulated:
            try:
                downloaded = await SSHController.download_file(
                    observer_vm, remote_pcap_path, local_pcap_path
                )
                if downloaded:
                    filename = os.path.basename(local_pcap_path)
                    return StorageService.upload_pcap_capture(filename, local_pcap_path)
            except Exception as exc:
                logger.warning(f"[CaptureManager] Real PCAP retrieval failed: {exc}")
                if os.getenv("TESTBED_REQUIRE_REAL_CAPTURE", "0") == "1":
                    raise RuntimeError(
                        "Real strongSwan PCAP capture was required but could not be retrieved "
                        f"from {observer_vm.host}: {exc}"
                    ) from exc

        if os.getenv("TESTBED_REQUIRE_REAL_CAPTURE", "0") == "1":
            raise RuntimeError(
                "Real strongSwan PCAP capture was required, but the observer capture was unavailable or empty."
            )

        # In simulated / offline mode or if remote fetch not available, copy appropriate sample capture
        profile = str(getattr(scenario, "traffic_profile", "") or "").upper()
        mode = str(getattr(scenario, "ipsec_mode", "tunnel") or "tunnel").lower()
        profile_mapping = CaptureManager.PROFILE_SAMPLE_MAP.get(profile)
        if isinstance(profile_mapping, dict):
            sample_source = profile_mapping.get(mode, profile_mapping.get("tunnel"))
        else:
            sample_source = profile_mapping

        sample_source = CaptureManager._resolve_sample_path(sample_source)
        if not sample_source:
            sample_source = CaptureManager._resolve_sample_path(CaptureManager.PROFILE_SAMPLE_MAP["DEFAULT"])

        if sample_source:
            shutil.copy2(sample_source, local_pcap_path)
            logger.info(f"[CaptureManager] Prepared PCAP artifact at {local_pcap_path}")
        else:
            raise FileNotFoundError("No bundled sample PCAP is available for the requested testbed scenario.")

        # Upload to storage
        filename = os.path.basename(local_pcap_path)
        download_url = StorageService.upload_pcap_capture(filename, local_pcap_path)
        return download_url

    @staticmethod
    def _resolve_sample_path(relative_path: Optional[str]) -> Optional[str]:
        if not relative_path:
            return None
        candidates = [
            Path(__file__).resolve().parents[2] / relative_path,
            Path.cwd() / relative_path,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return None
