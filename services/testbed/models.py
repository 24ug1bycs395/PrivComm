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
    # Optional control-plane endpoint used to reach a VM through Docker port
    # forwarding while keeping `host` as the VM's internal VPN address.
    ssh_host: Optional[str] = None
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
    hash_algorithm: str = "SHA-256"  # "SHA-256", "SHA-384", "SHA-512", "MD5", "SHA-1" (used for handshake integrity verification & IKE/ESP PRF)
    dh_group: str = "19 (ECP-256)"  # "19 (ECP-256)", "14 (MODP-2048)", "2 (MODP-1024)"
    pfs: bool = True
    esp_enabled: bool = True
    auth_method: str = "PSK"  # "PSK", "RSA-Cert", "EAP-MSCHAPv2"
    pre_shared_key: str = "CyberSentinelSecureKey2026!"
    # Tunnel or Transport mode — both fully supported in config generation
    ipsec_mode: str = "tunnel"  # "tunnel" or "transport"
    # IP version of the VPN endpoints — both IPv4 and IPv6 are supported
    ip_version: str = "IPv4"  # "IPv4" or "IPv6"
    # Traffic profile — controls synthetic traffic injected during the testbed run
    # Supported: ICMP_ECHO, HTTP_GET, IPERF_BURST, VOIP_RTP,
    #            VIDEO_STREAM, EMAIL_SMTP, DNS_BURST, P2P_SIM
    traffic_profile: str = "ICMP_ECHO"
    payload_type: Optional[str] = None
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
    # ── Multi-Tunnel / Hub & Spoke ──────────────────────────────────────────
    ScenarioDefinition(
        id="multi-tunnel-hub-spoke-mesh",
        name="Multi-Tunnel Hub & Spoke Mesh (HQ ↔ Branch Alpha & Beta)",
        description="Concurrent multi-tunnel execution orchestrating 2 parallel IPsec SAs: Tunnel 1 (Compliant IKEv2 / AES-256-GCM) and Tunnel 2 (Legacy IKEv1 / 3DES Drift). Demonstrates multi-SA audit.",
        ike_version="IKEv2 + IKEv1",
        encryption="AES-256-GCM / 3DES-CBC",
        integrity="None (AEAD) / MD5",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256) / Group 2",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="HTTP_GET",
        traffic_duration_sec=8,
        packet_count=55,
        is_weak_compliance=False
    ),
    # ── Tunnel Mode / IPv4 ──────────────────────────────────────────────────
    ScenarioDefinition(
        id="ikev2-aes-gcm-compliant",
        name="IKEv2 AES-256-GCM Tunnel / IPv4 (Zero-Trust Compliant)",
        description="Modern site-to-site IPsec tunnel using IKEv2 with AES-256-GCM (AEAD), DH Group 19 (ECP-256), and PFS. Traffic profile: HTTP web browsing.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="HTTP_GET",
        traffic_duration_sec=6,
        packet_count=35,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev1-3des-legacy-weak",
        name="IKEv1 Aggressive Mode 3DES-MD5 (High Risk / Deprecated)",
        description="Legacy enterprise configuration with IKEv1 Aggressive Mode, 3DES encryption, MD5 hashing, weak DH Group 2 (1024-bit), and PFS disabled. Demonstrates policy violation flags.",
        ike_version="IKEv1",
        encryption="3DES-CBC",
        integrity="MD5",
        hash_algorithm="MD5",
        dh_group="2 (MODP-1024)",
        pfs=False,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="ICMP_ECHO",
        traffic_duration_sec=5,
        packet_count=20,
        is_weak_compliance=True
    ),
    ScenarioDefinition(
        id="ikev2-cnsa-suite-b",
        name="IKEv2 Suite-B / CNSA Top-Secret Profile (Tunnel / IPv4)",
        description="Strict NSA CNSA Suite profile using AES-256-GCM, SHA-384, DH Group 20 (ECP-384). Traffic profile: iperf3 file-transfer burst.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="SHA384",
        hash_algorithm="SHA-384",
        dh_group="20 (ECP-384)",
        pfs=True,
        auth_method="RSA-Cert",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="IPERF_BURST",
        traffic_duration_sec=8,
        packet_count=50,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-rekey-stress",
        name="IKEv2 Rapid Rekeying & Lifecycle Stress Test",
        description="Tunnel with 20-second IKE SA / CHILD SA rekey intervals to capture CREATE_CHILD_SA exchanges and SPI rotations.",
        ike_version="IKEv2",
        encryption="AES-128-CBC",
        integrity="SHA256",
        hash_algorithm="SHA-256",
        dh_group="14 (MODP-2048)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="ICMP_ECHO",
        traffic_duration_sec=10,
        packet_count=40,
        is_weak_compliance=False
    ),

    # ── Transport Mode / IPv4 ───────────────────────────────────────────────
    ScenarioDefinition(
        id="ikev2-transport-aes-gcm",
        name="IKEv2 AES-256-GCM Transport Mode / IPv4",
        description="IPsec Transport Mode (host-to-host): original IP headers visible, only payload is encrypted. Uses AES-256-GCM and DH Group 19. Traffic: VoIP RTP UDP stream.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="transport",
        ip_version="IPv4",
        traffic_profile="VOIP_RTP",
        traffic_duration_sec=6,
        packet_count=30,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-transport-aes-cbc",
        name="IKEv2 AES-256-CBC Transport Mode / IPv4",
        description="IPsec Transport Mode with AES-256-CBC + HMAC-SHA2-256. Demonstrates metadata exposure of source/destination IPs in Transport Mode. Traffic: Email SMTP.",
        ike_version="IKEv2",
        encryption="AES-256-CBC",
        integrity="SHA256",
        hash_algorithm="SHA-256",
        dh_group="14 (MODP-2048)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="transport",
        ip_version="IPv4",
        traffic_profile="EMAIL_SMTP",
        traffic_duration_sec=5,
        packet_count=25,
        is_weak_compliance=False
    ),

    # ── IPv6 Tunnel Mode ────────────────────────────────────────────────────
    ScenarioDefinition(
        id="ikev2-ipv6-tunnel-aes-gcm",
        name="IKEv2 AES-256-GCM Tunnel Mode / IPv6",
        description="Modern IPsec VPN over IPv6 using IKEv2 with AES-256-GCM (AEAD) and DH Group 20 (ECP-384). Validates IPv6 endpoint detection and flow feature extraction. Traffic: DNS burst.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-384",
        dh_group="20 (ECP-384)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv6",
        traffic_profile="DNS_BURST",
        traffic_duration_sec=6,
        packet_count=30,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-ipv6-transport-aes-gcm",
        name="IKEv2 AES-256-GCM Transport Mode / IPv6",
        description="Host-to-host IPsec Transport Mode over IPv6. Shows IPv6 header visibility and metadata exposure in Transport Mode. Traffic: P2P simulation.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="transport",
        ip_version="IPv6",
        traffic_profile="P2P_SIM",
        traffic_duration_sec=8,
        packet_count=40,
        is_weak_compliance=False
    ),

    # ── Diverse Traffic Profiles (Tunnel / IPv4) ────────────────────────────
    ScenarioDefinition(
        id="ikev2-voip-tunnel",
        name="IKEv2 Tunnel — VoIP / WhatsApp Voice Traffic",
        description="IPsec Tunnel with VoIP RTP UDP stream simulation to train and validate the XGBoost VoIP classifier. Uses AES-256-GCM for low-latency AEAD encryption.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="VOIP_RTP",
        traffic_duration_sec=8,
        packet_count=60,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-video-streaming",
        name="IKEv2 Tunnel — Video Streaming Traffic",
        description="IPsec Tunnel with large-packet UDP stream simulating video streaming (YouTube / Netflix). High byte-rate, bursty pattern. Uses AES-256-GCM.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="VIDEO_STREAM",
        traffic_duration_sec=10,
        packet_count=80,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-email-tunnel",
        name="IKEv2 Tunnel — Email / SMTP Traffic",
        description="IPsec Tunnel with SMTP email traffic simulation. Low-rate, connection-oriented pattern. Uses AES-256-CBC + HMAC-SHA2-256.",
        ike_version="IKEv2",
        encryption="AES-256-CBC",
        integrity="SHA256",
        hash_algorithm="SHA-256",
        dh_group="14 (MODP-2048)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="EMAIL_SMTP",
        traffic_duration_sec=6,
        packet_count=25,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-dns-tunnel",
        name="IKEv2 Tunnel — DNS Query Burst Traffic",
        description="IPsec Tunnel with rapid DNS UDP query burst. Small-packet, high-rate pattern. Uses AES-256-GCM. Validates DNS fingerprinting resistance.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="DNS_BURST",
        traffic_duration_sec=5,
        packet_count=50,
        is_weak_compliance=False
    ),
    ScenarioDefinition(
        id="ikev2-p2p-tunnel",
        name="IKEv2 Tunnel — P2P / BitTorrent Traffic Simulation",
        description="IPsec Tunnel with bidirectional iperf3 UDP stream simulating P2P file sharing. High bidirectional byte rate and large forward/backward IAT asymmetry.",
        ike_version="IKEv2",
        encryption="AES-256-GCM",
        integrity="None (AEAD)",
        hash_algorithm="SHA-256",
        dh_group="19 (ECP-256)",
        pfs=True,
        auth_method="PSK",
        ipsec_mode="tunnel",
        ip_version="IPv4",
        traffic_profile="P2P_SIM",
        traffic_duration_sec=10,
        packet_count=60,
        is_weak_compliance=False
    ),
]

