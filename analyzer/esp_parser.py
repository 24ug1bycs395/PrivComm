import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def parse_esp_scapy(packets: List[Any]) -> Dict[str, Any]:
    """Extract ESP and AH details using Scapy layer analysis.
    Supports both IPv4 (proto 50/51) and IPv6 (next header 50/51).
    """
    esp_count = 0
    ah_count = 0
    esp_bytes = 0
    ah_bytes = 0
    spis = set()
    ip_versions_seen = set()

    from scapy.all import IP, IPv6, ESP, AH

    for pkt in packets:
        # ── IPv4 ──────────────────────────────────────────────────────────────
        if pkt.haslayer(IP):
            ip_layer = pkt[IP]
            ip_versions_seen.add("IPv4")
            proto = ip_layer.proto

            if proto == 50 or pkt.haslayer(ESP):
                esp_count += 1
                esp_bytes += len(pkt)
                if pkt.haslayer(ESP):
                    spi_val = getattr(pkt[ESP], "spi", None)
                    if spi_val is not None:
                        spi_hex = spi_val.hex() if isinstance(spi_val, bytes) else f"{spi_val:08x}"
                        spis.add(f"0x{spi_hex}")

            elif proto == 51 or pkt.haslayer(AH):
                ah_count += 1
                ah_bytes += len(pkt)
                if pkt.haslayer(AH):
                    spi_val = getattr(pkt[AH], "spi", None)
                    if spi_val is not None:
                        spi_hex = spi_val.hex() if isinstance(spi_val, bytes) else f"{spi_val:08x}"
                        spis.add(f"0x{spi_hex}")

        # ── IPv6 ──────────────────────────────────────────────────────────────
        elif pkt.haslayer(IPv6):
            ip6_layer = pkt[IPv6]
            ip_versions_seen.add("IPv6")
            # Scapy resolves the next-header chain; check for ESP/AH layers
            if pkt.haslayer(ESP):
                esp_count += 1
                esp_bytes += len(pkt)
                spi_val = getattr(pkt[ESP], "spi", None)
                if spi_val is not None:
                    spi_hex = spi_val.hex() if isinstance(spi_val, bytes) else f"{spi_val:08x}"
                    spis.add(f"0x{spi_hex}")
            elif pkt.haslayer(AH):
                ah_count += 1
                ah_bytes += len(pkt)
                spi_val = getattr(pkt[AH], "spi", None)
                if spi_val is not None:
                    spi_hex = spi_val.hex() if isinstance(spi_val, bytes) else f"{spi_val:08x}"
                    spis.add(f"0x{spi_hex}")
            # Also check nh field directly for raw IPv6 + ESP without Scapy dissection
            elif ip6_layer.nh == 50:
                esp_count += 1
                esp_bytes += len(pkt)
            elif ip6_layer.nh == 51:
                ah_count += 1
                ah_bytes += len(pkt)

    # Determine detected IP version(s)
    if "IPv4" in ip_versions_seen and "IPv6" in ip_versions_seen:
        detected_ip_version = "Dual-Stack"
    elif "IPv6" in ip_versions_seen:
        detected_ip_version = "IPv6"
    elif "IPv4" in ip_versions_seen:
        detected_ip_version = "IPv4"
    else:
        detected_ip_version = "unknown"

    return {
        "esp_detected": esp_count > 0,
        "ah_detected": ah_count > 0,
        "esp_packet_count": esp_count,
        "ah_packet_count": ah_count,
        "esp_bytes": esp_bytes,
        "ah_bytes": ah_bytes,
        "observed_spis": list(spis),
        "detected_ip_version": detected_ip_version,
    }


def parse_esp_tshark_json(tshark_packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract ESP and AH details using TShark JSON dissection.
    Detects both IPv4 and IPv6 encapsulation.
    """
    esp_count = 0
    ah_count = 0
    spis = set()
    ip_versions_seen = set()

    for pkt in tshark_packets:
        layers = pkt.get("_source", {}).get("layers", {})

        # IP version detection
        if "ip" in layers:
            ip_versions_seen.add("IPv4")
        if "ipv6" in layers:
            ip_versions_seen.add("IPv6")

        if "esp" in layers:
            esp_count += 1
            esp_layer = layers["esp"]
            if "esp.spi" in esp_layer:
                spis.add(str(esp_layer["esp.spi"]))

        if "ah" in layers:
            ah_count += 1
            ah_layer = layers["ah"]
            if "ah.spi" in ah_layer:
                spis.add(str(ah_layer["ah.spi"]))

    if "IPv4" in ip_versions_seen and "IPv6" in ip_versions_seen:
        detected_ip_version = "Dual-Stack"
    elif "IPv6" in ip_versions_seen:
        detected_ip_version = "IPv6"
    elif "IPv4" in ip_versions_seen:
        detected_ip_version = "IPv4"
    else:
        detected_ip_version = "unknown"

    return {
        "esp_detected": esp_count > 0,
        "ah_detected": ah_count > 0,
        "esp_packet_count": esp_count,
        "ah_packet_count": ah_count,
        "observed_spis": list(spis),
        "detected_ip_version": detected_ip_version,
    }
