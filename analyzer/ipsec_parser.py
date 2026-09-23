import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def synthesize_ipsec_config(ike_info: Dict[str, Any], esp_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesize IKE and ESP parsing results into normalized IPsec configuration output.
    Follows Section 5 & 20 strict non-invention rules: missing parameters stay 'unknown'.
    """
    ipsec_detected = ike_info.get("ike_detected", False) or esp_info.get("esp_detected", False) or esp_info.get("ah_detected", False)

    # Integrity setting: If encryption is AEAD (e.g., GCM), integrity is provided by AEAD
    enc = ike_info.get("encryption", "unknown")
    integrity = ike_info.get("integrity", "unknown")
    if "GCM" in str(enc) or "CCM" in str(enc):
        integrity = "AEAD"

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
        "mode": "Tunnel" if (esp_info.get("esp_detected") and ike_info.get("ike_detected")) else "unknown",
        "pfs": "unknown",  # Cannot be definitively inferred without decrypting/observing SA renegotiation
        "replay_protection": "unknown", # Replay window size is unobservable without ESP decryption
        "sa_lifetime": None,
        "initiator_spi": ike_info.get("initiator_spi"),
        "responder_spi": ike_info.get("responder_spi"),
        "esp_spis": esp_info.get("observed_spis", [])
    }

    return config
