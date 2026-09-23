import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def parse_esp_scapy(packets: List[Any]) -> Dict[str, Any]:
    """Extract ESP and AH details using Scapy layer analysis."""
    esp_count = 0
    ah_count = 0
    esp_bytes = 0
    ah_bytes = 0
    spis = set()

    from scapy.all import IP, ESP, AH

    for pkt in packets:
        if pkt.haslayer(IP):
            ip_layer = pkt[IP]
            proto = ip_layer.proto

            if proto == 50 or pkt.haslayer(ESP):
                esp_count += 1
                esp_bytes += len(pkt)
                if pkt.haslayer(ESP):
                    esp_layer = pkt[ESP]
                    spi_val = getattr(esp_layer, "spi", None)
                    if spi_val is not None:
                        spi_hex = spi_val.hex() if isinstance(spi_val, bytes) else f"{spi_val:08x}"
                        spis.add(f"0x{spi_hex}")

            elif proto == 51 or pkt.haslayer(AH):
                ah_count += 1
                ah_bytes += len(pkt)
                if pkt.haslayer(AH):
                    ah_layer = pkt[AH]
                    spi_val = getattr(ah_layer, "spi", None)
                    if spi_val is not None:
                        spi_hex = spi_val.hex() if isinstance(spi_val, bytes) else f"{spi_val:08x}"
                        spis.add(f"0x{spi_hex}")

    return {
        "esp_detected": esp_count > 0,
        "ah_detected": ah_count > 0,
        "esp_packet_count": esp_count,
        "ah_packet_count": ah_count,
        "esp_bytes": esp_bytes,
        "ah_bytes": ah_bytes,
        "observed_spis": list(spis)
    }

def parse_esp_tshark_json(tshark_packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract ESP and AH details using TShark JSON dissection."""
    esp_count = 0
    ah_count = 0
    spis = set()

    for pkt in tshark_packets:
        layers = pkt.get("_source", {}).get("layers", {})
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

    return {
        "esp_detected": esp_count > 0,
        "ah_detected": ah_count > 0,
        "esp_packet_count": esp_count,
        "ah_packet_count": ah_count,
        "observed_spis": list(spis)
    }
