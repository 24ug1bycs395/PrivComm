from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ProtocolAnalysisResult(BaseModel):
    ipsec_detected: bool = Field(default=False, description="Indicates if IPsec / IKE / ESP / AH was identified")
    ike_version: Optional[str] = Field(default=None, description="IKE version detected (e.g. 'IKEv1', 'IKEv2')")
    esp_detected: bool = Field(default=False, description="True if ESP (Encapsulating Security Payload, IP proto 50) is detected")
    ah_detected: bool = Field(default=False, description="True if AH (Authentication Header, IP proto 51) is detected")
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
    report_html: Optional[str] = Field(default=None, description="Generated Executive HTML report path or download link")

