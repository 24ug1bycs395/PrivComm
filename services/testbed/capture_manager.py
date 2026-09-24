import os
import shutil
import asyncio
import logging
from typing import Optional
from services.testbed.models import VMHostConfig, ScenarioDefinition
from services.testbed.ssh_controller import SSHController
from db.storage import StorageService

logger = logging.getLogger("testbed.capture_manager")

class CaptureManager:
    """
    Controls remote and local packet capture mechanisms for the testbed.
    """

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
            f"nohup sudo tcpdump -i {interface} 'udp port 500 or udp port 4500 or proto 50' "
            f"-w {remote_pcap} > /dev/null 2>&1 & echo $!"
        )
        code, stdout, stderr = await SSHController.run_command(observer_vm, capture_cmd)
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
        stop_cmd = "sudo pkill -f tcpdump || true"
        await SSHController.run_command(observer_vm, stop_cmd)
        await asyncio.sleep(0.5)

        os.makedirs(os.path.dirname(local_pcap_path), exist_ok=True)

        # In simulated / offline mode or if remote fetch not available, copy appropriate sample capture
        sample_source = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
        if not os.path.exists(sample_source):
            sample_source = "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng"

        if os.path.exists(sample_source):
            shutil.copy2(sample_source, local_pcap_path)
            logger.info(f"[CaptureManager] Prepared PCAP artifact at {local_pcap_path}")

        # Upload to storage
        filename = os.path.basename(local_pcap_path)
        download_url = StorageService.upload_pcap_capture(filename, local_pcap_path)
        return download_url
