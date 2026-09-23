from pydantic import BaseModel, Field
from typing import Optional


class ProtocolAnalysisResult(BaseModel):
    ipsec_detected: bool = Field(default=False, description="Indicates if IPsec / IKE / ESP / AH was identified")
    ike_version: Optional[str] = Field(default=None, description="IKE version detected (e.g. 'IKEv1', 'IKEv2')")
    esp_detected: bool = Field(default=False, description="True if ESP (Encapsulating Security Payload, IP proto 50) is detected")
    ah_detected: bool = Field(default=False, description="True if AH (Authentication Header, IP proto 51) is detected")
    mode: Optional[str] = Field(default=None, description="IPsec encapsulation mode ('Tunnel' or 'Transport')")
    encryption: Optional[str] = Field(default=None, description="Identified encryption cipher algorithm (e.g. 'AES-256-GCM', 'AES-CBC-256', '3DES-CBC')")
    integrity: Optional[str] = Field(default=None, description="Identified integrity / PRF / HMAC algorithm (e.g. 'HMAC-SHA2-256', 'AEAD', 'MD5')")
    dh_group: Optional[str] = Field(default=None, description="Diffie-Hellman Group identifier (e.g. '14', '19', '2')")
    pfs: Optional[bool] = Field(default=None, description="Perfect Forward Secrecy enforcement detected")
    replay_protection: Optional[bool] = Field(default=None, description="Anti-replay window sequence tracking detected")
    ip_version: Optional[str] = Field(default=None, description="IP version of the IPsec traffic ('IPv4' or 'IPv6')")
    source_ip: Optional[str] = Field(default=None, description="Source IP address of the IPsec tunnel endpoint")
    destination_ip: Optional[str] = Field(default=None, description="Destination IP address of the IPsec tunnel endpoint")
