"""Emit raw structured JSON for the live testbed parameter-inspection terminal."""

import json
from typing import Any, Dict, List, Optional

from services.testbed.models import ScenarioDefinition, TestbedTopology


TRAFFIC_LABELS = {
    "ICMP_ECHO": "ICMP",
    "HTTP_GET": "Web browsing",
    "VOIP_RTP": "VoIP / WhatsApp voice",
    "VIDEO_STREAM": "Video streaming",
    "EMAIL_SMTP": "Email / SMTP",
    "DNS_BURST": "DNS query burst",
    "P2P_SIM": "P2P / BitTorrent simulation",
    "IPERF_BURST": "File transfer / iperf3",
}


def _detected_value(analysis: Optional[Any], field: str, fallback: Any) -> Any:
    value = getattr(analysis, field, None) if analysis is not None else None
    return fallback if value in (None, "", "unknown") else value


def build_parameter_payload(
    scenario: ScenarioDefinition,
    topology: TestbedTopology,
    analysis: Optional[Any] = None,
    source: str = "scenario_configuration",
) -> Dict[str, Any]:
    """Build a JSON-serializable configuration or post-PCAP detection payload."""
    encryption = str(_detected_value(analysis, "encryption", scenario.encryption) or "Unknown")
    mode = str(_detected_value(analysis, "mode", scenario.ipsec_mode.capitalize()) or "Unknown")
    ip_version = str(_detected_value(analysis, "ip_version", scenario.ip_version) or "Unknown")
    dh_group = _detected_value(analysis, "dh_group", scenario.dh_group)
    pfs = bool(_detected_value(analysis, "pfs", scenario.pfs))
    encryption_upper = encryption.upper()
    traffic_profile = (scenario.traffic_profile or "UNKNOWN").upper()

    return {
        "source": source,
        "ikeVersion": _detected_value(analysis, "ike_version", scenario.ike_version),
        "ipsec": {
            "tunnelMode": mode.upper() == "TUNNEL",
            "transportMode": mode.upper() == "TRANSPORT",
            "mode": mode,
            "ipVersion": ip_version,
        },
        "cryptography": {
            "encryption": encryption,
            "aes128": "AES-128" in encryption_upper,
            "aes256": "AES-256" in encryption_upper,
            "aesGcm": "GCM" in encryption_upper,
            "aesCbcHmac": "CBC" in encryption_upper,
            "integrity": _detected_value(analysis, "integrity", scenario.hash_algorithm or scenario.integrity),
            "dhGroup": dh_group,
            "perfectForwardSecrecy": pfs,
        },
        "endpoints": {
            "initiator": topology.initiator.host,
            "responder": topology.responder.host,
            "observer": topology.observer.host,
        },
        "traffic": {
            "profile": traffic_profile,
            "label": TRAFFIC_LABELS.get(traffic_profile, traffic_profile),
            "packetCount": scenario.packet_count,
            "durationSeconds": scenario.traffic_duration_sec,
        },
    }


def format_json_payload(payload: Dict[str, Any]) -> List[str]:
    """Return pretty-printed JSON lines for a terminal event stream."""
    return json.dumps(payload, indent=2, ensure_ascii=True).splitlines()


if __name__ == "__main__":
    print(json.dumps({"status": "PrivComm IPsec parameter inspector is loaded"}, indent=2))
