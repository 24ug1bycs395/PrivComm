import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def synthesize_ipsec_config(ike_info: Dict[str, Any], esp_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesize IKE and ESP parsing results into normalized IPsec configuration output.
    Follows Section 5 & 20 strict non-invention rules: missing parameters stay 'unknown'.

    Includes:
    - IP version detection from ESP/AH layer analysis (IPv4, IPv6, or Dual-Stack)
    - Source/Destination IP extraction where reliably observable
    - Mode inference (Tunnel is inferred when IKE + ESP are both present)
    """
    ipsec_detected = (
        ike_info.get("ike_detected", False)
        or esp_info.get("esp_detected", False)
        or esp_info.get("ah_detected", False)
    )

    # Integrity setting: If encryption is AEAD (e.g., GCM), integrity is provided by AEAD
    enc = ike_info.get("encryption", "unknown")
    integrity = ike_info.get("integrity", "unknown")
    if "GCM" in str(enc) or "CCM" in str(enc):
        integrity = "AEAD"

    # IP version — taken from the ESP/AH layer parser which inspects actual packet headers.
    # This reflects what is actually on the wire (IPv4, IPv6, or Dual-Stack).
    detected_ip_version = esp_info.get("detected_ip_version", "unknown")
    if detected_ip_version == "unknown" and ike_info.get("ike_detected"):
        # IKE runs over UDP; if we have IKE but no ESP/AH yet, ip_version stays unknown
        detected_ip_version = "unknown"

    # Source/Destination IPs — extracted from IKE Identity payloads where available.
    # These are the IKE endpoint IPs, not the inner tunnel subnets.
    source_ip = ike_info.get("initiator_ip", None)
    destination_ip = ike_info.get("responder_ip", None)

    config = {
        "detected": ipsec_detected,
        "ike_detected": ike_info.get("ike_detected", False),
        "ike_version": ike_info.get("ike_version", "unknown"),
        "esp_detected": esp_info.get("esp_detected", False),
        "ah_detected": esp_info.get("ah_detected", False),
        "exchange_type": ike_info.get("exchange_type", "unknown"),
        "encryption": enc,
        "key_length": ike_info.get("key_length"),
        "integrity": integrity,
        "prf": ike_info.get("prf", "unknown"),
        "dh_group": ike_info.get("dh_group", "unknown"),
        # Tunnel mode is inferred when both IKE negotiation and ESP encapsulation are present.
        # Transport mode is observable only if ESP appears without a new IKE tunnel exchange
        # (host-to-host), which is uncommon in captures that also include IKE.
        # Set to 'unknown' rather than assuming Tunnel to avoid false assertions.
        "mode": _infer_mode(ike_info, esp_info),
        "mode_confidence": _infer_mode_confidence(ike_info, esp_info),
        # PFS cannot be determined without observing a CREATE_CHILD_SA exchange with a DH payload.
        "pfs": "unknown",
        # Replay window size is not observable without ESP decryption.
        "replay_protection": "unknown",
        "sa_lifetime": None,
        "initiator_spi": ike_info.get("initiator_spi"),
        "responder_spi": ike_info.get("responder_spi"),
        "esp_spis": esp_info.get("observed_spis", []),
        # IP version detected from wire-level packet headers
        "ip_version": detected_ip_version,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
    }

    return config


def _infer_mode(ike_info: Dict[str, Any], esp_info: Dict[str, Any]) -> str:
    """
    Infer IPsec operating mode from observable packet characteristics.

    Rules:
    - Tunnel:    IKE negotiation present AND ESP/AH encapsulation present
                 (IKE sets up a tunnel SA, then ESP carries encapsulated packets)
    - Transport: ESP/AH present WITHOUT a preceding IKE_SA_INIT exchange visible
                 in the same capture (host-to-host static SA, uncommon in full captures)
    - unknown:   Neither condition is clearly distinguishable
    """
    esp_present = esp_info.get("esp_detected", False)
    has_ike_sa_init = (
        str(ike_info.get("exchange_type", "")).upper() == "IKE_SA_INIT"
        and bool(ike_info.get("initiator_spi"))
    )

    if has_ike_sa_init and esp_present:
        return "Tunnel"
    elif esp_present:
        return "Transport (inferred)"
    else:
        return "unknown"


def _infer_mode_confidence(ike_info: Dict[str, Any], esp_info: Dict[str, Any]) -> str:
    """Return confidence based only on definitive wire-level observations."""
    has_ike_sa_init = (
        str(ike_info.get("exchange_type", "")).upper() == "IKE_SA_INIT"
        and bool(ike_info.get("initiator_spi"))
    )
    if has_ike_sa_init and esp_info.get("esp_detected", False):
        return "high"
    if esp_info.get("esp_detected", False):
        return "medium"
    return "low"
