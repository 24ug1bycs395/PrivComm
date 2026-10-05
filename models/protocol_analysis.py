from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProtocolAnalysisResult(BaseModel):
    ipsec_detected: bool = Field(default=False, description="Indicates if IPsec / IKE / ESP / AH was identified")
    ike_version: Optional[str] = Field(default=None, description="IKE version detected (e.g. 'IKEv1', 'IKEv2')")
    esp_detected: Optional[bool] = Field(default=False, description="Whether ESP (IP protocol 50) was detected; null when no packet capture was analyzed")
    ah_detected: Optional[bool] = Field(default=False, description="Whether AH (IP protocol 51) was detected; null when no packet capture was analyzed")
    mode: Optional[str] = Field(default=None, description="IPsec encapsulation mode ('Tunnel' or 'Transport')")
    mode_confidence: Optional[str] = Field(default=None, description="Confidence in inferred IPsec mode: high, medium, or low")
    encryption: Optional[str] = Field(default=None, description="Identified encryption cipher algorithm (e.g. 'AES-256-GCM', 'AES-CBC-256', '3DES-CBC')")
    integrity: Optional[str] = Field(default=None, description="Identified integrity / PRF / HMAC algorithm (e.g. 'HMAC-SHA2-256', 'AEAD', 'MD5')")
    dh_group: Optional[str] = Field(default=None, description="Diffie-Hellman Group identifier (e.g. '14', '19', '2')")
    pfs: Optional[bool] = Field(default=None, description="Perfect Forward Secrecy enforcement detected")
    replay_protection: Optional[bool] = Field(default=None, description="Anti-replay window sequence tracking detected")
    ip_version: Optional[str] = Field(default=None, description="IP version of the IPsec traffic ('IPv4' or 'IPv6')")
    source_ip: Optional[str] = Field(default=None, description="Source IP address of the IPsec tunnel endpoint")
    destination_ip: Optional[str] = Field(default=None, description="Destination IP address of the IPsec tunnel endpoint")

    # Extended AI Traffic, Metadata Exposure, Behavioral Anomaly & Security Assessment Fields
    traffic_classification: Optional[Dict[str, Any]] = Field(default=None, description="XGBoost AI encrypted traffic classification result")
    behavioral_anomaly: Optional[Dict[str, Any]] = Field(default=None, description="VPN Behavioral Anomaly Detection result")
    metadata_exposure: Optional[Dict[str, Any]] = Field(default=None, description="Observable metadata exposure assessment (IPs, identities, SPI linkability, transport mode exposure)")
    security_assessment: Optional[Dict[str, Any]] = Field(default=None, description="Security policy audit findings and risk evaluation")
    explainability: Optional[List[Dict[str, Any]]] = Field(default=None, description="Plain-English component-by-component security explanations")
    tunnel_integrity: Optional[Dict[str, Any]] = Field(default=None, description="Testbed handshake-integrity attestation status; configured values alone are not verification")
    rfc4303_elimination: Optional[Dict[str, Any]] = Field(default=None, description="ESP length arithmetic cipher elimination result")
    data_provenance: Dict[str, str] = Field(
        default_factory=dict,
        description="How each analysis field was obtained: OBSERVED, PARSED, INFERRED, or UNKNOWN",
    )
    capture_sha256: Optional[str] = Field(default=None, description="SHA-256 digest of the analyzed capture")
    packet_evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Observed packet fields with frame numbers and zero-based, half-open capture byte ranges",
    )
    downgrade_tracking: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional historical per-tunnel baseline comparison; unknown values are not treated as downgrades",
    )
    crypto_bom: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Capture-backed PrivComm cryptographic bill of materials; unknown algorithms are excluded and listed separately",
    )
    vendor: Optional[str] = Field(default=None, description="Router/Firewall vendor (e.g. Cisco ASA, Fortinet FortiOS, pfSense, Libreswan, strongSwan)")
    remediation_config: Optional[str] = Field(default=None, description="Vendor-tailored hardened production configuration snippet")
    raw_config_lines: Optional[int] = Field(default=None, description="Number of lines in the parsed vendor config")
    analysis_source: Optional[str] = Field(default=None, description="Input analyzed, such as pcap or vendor_config")
    report_html: Optional[str] = Field(default=None, description="Generated Executive HTML report path or download link")
