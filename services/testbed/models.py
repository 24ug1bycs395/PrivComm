from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TestbedState(str, Enum):
    QUEUED = "QUEUED"
    PROVISIONING = "PROVISIONING"
    CAPTURING = "CAPTURING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VMHostConfig(BaseModel):
    host: str = "192.168.56.10"
    port: int = 22
    username: str = "vagrant"
    password: Optional[str] = "vagrant"
    key_path: Optional[str] = None
    interface: str = "eth1"
    is_simulated: bool = False


class TestbedTopology(BaseModel):
    initiator: VMHostConfig = Field(
        default_factory=lambda: VMHostConfig(host="192.168.56.10", username="vagrant", interface="eth1")
    )
    responder: VMHostConfig = Field(
        default_factory=lambda: VMHostConfig(host="192.168.56.20", username="vagrant", interface="eth1")
    )
    observer: VMHostConfig = Field(
        default_factory=lambda: VMHostConfig(host="192.168.56.30", username="vagrant", interface="eth1")
    )


class ScenarioDefinition(BaseModel):
    id: str
    name: str
    description: str
    ike_version: str = "IKEv2"  # "IKEv2", "IKEv1", "IKEv1_Aggressive"
    encryption: str = "AES-256-GCM"  # "AES-256-GCM", "AES-256-CBC", "3DES-CBC", "AES-128-CBC"
    integrity: str = "SHA384"  # "SHA384", "SHA256", "MD5", "None (AEAD)"
    dh_group: str = "19 (ECP-256)"  # "19 (ECP-256)", "14 (MODP-2048)", "2 (MODP-1024)"
    pfs: bool = True
    auth_method: str = "PSK"  # "PSK", "RSA-Cert", "EAP-MSCHAPv2"
    pre_shared_key: str = "CyberSentinelSecureKey2026!"
    traffic_profile: str = "ICMP_ECHO"  # "ICMP_ECHO", "HTTP_GET", "IPERF_BURST"
    traffic_duration_sec: int = 5
    packet_count: int = 20
    is_weak_compliance: bool = False


class TestbedRunRequest(BaseModel):
    scenario_id: Optional[str] = "ikev2-aes-gcm-compliant"
    custom_scenario: Optional[ScenarioDefinition] = None
    topology: Optional[TestbedTopology] = None


class TestbedJobStatus(BaseModel):
    job_id: str
    scenario_name: str
    state: TestbedState
    progress_pct: int
    current_step: str
    logs: List[str] = []
    pcap_download_url: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# Standard Scenarios Library
PRESET_SCENARIOS: List[ScenarioDefinition] = [
    ScenarioDefinition(
        id="ikev2-aes-gcm-compliant",
        name="IKEv2 AES-256-GCM (Zero-Trust Compliant)",
        description="Modern site-to-site IPsec tunnel utilizing IKEv2 with authenticated AEAD cipher suite (AES-256-GCM), Diffie-Hellman Group 19 (ECP-256), and Perfect Forward Secrecy.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        traffic_profile="HTTP_GET",
        traffic_duration_sec=6,
        packet_count=35,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev1-3des-legacy-weak",
        name="IKEv1 Aggressive Mode with 3DES-MD5 (High Risk / Deprecated)",
        description="Legacy enterprise configuration with IKEv1 Aggressive Mode, 3DES encryption, MD5 hashing, and weak DH Group 2 (1024-bit). Demonstrates policy violation flags and downgrade risks.",
        ike_version="IKEv1",
        encryption="3DES-CBC",
        integrity="MD5",
        dh_group="2 (MODP-1024)",
        pfs=False,
        auth_method="PSK",
        traffic_profile="ICMP_ECHO",
        traffic_duration_sec=5,
        packet_count=20,
        is_weak_compliance=True
    ),
    ScenarioDefinition(
        id="ikev2-cnsa-suite-b",
        name="IKEv2 Suite-B / CNSA Top-Secret Profile",
        description="Strict NSA Commercial National Security Algorithm (CNSA) Suite profile using AES-256-GCM, SHA-384 integrity, and DH Group 20 (ECP-384).",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="SHA384",
        dh_group="20 (ECP-384)",
        pfs=True,
        auth_method="RSA-Cert",
        traffic_profile="IPERF_BURST",
        traffic_duration_sec=8,
        packet_count=50,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-rekey-stress",
        name="IKEv2 Rapid Rekeying & Lifecycle Stress Test",
        description="Tunnel configured with 20-second IKE SA / CHILD SA rekey intervals to capture IKE_CREATE_CHILD_SA exchanges, SPI rotations, and cryptographic lifecycle verification.",
        ike_version="IKEv2",
        encryption="AES-128-CBC",
        integrity="SHA256",
        dh_group="14 (MODP-2048)",
        pfs=True,
        auth_method="PSK",
        traffic_profile="ICMP_ECHO",
        traffic_duration_sec=10,
        packet_count=40,
        is_weak_compliance=False
    )
]
