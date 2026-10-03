import logging
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Standard IKE Identity Payload types (RFC 7296 / RFC 2407)
ID_TYPES = {
    1: "ID_IPV4_ADDR",
    2: "ID_FQDN",
    3: "ID_RFC822_ADDR",
    5: "ID_IPV6_ADDR",
    9: "ID_DER_ASN1_DN",
    11: "ID_KEY_ID"
}


def _extract_endpoint_ips(
    packets: Optional[List[Any]] = None,
    tshark_packets: Optional[List[Dict[str, Any]]] = None
) -> Tuple[Optional[str], Optional[str], str, Set[str], Set[str]]:
    """
    Extract outer source and destination IP addresses from Scapy or TShark packet collections.
    """
    source_ip = None
    destination_ip = None
    ip_ver = "IPv4"
    unique_srcs: Set[str] = set()
    unique_dsts: Set[str] = set()

    if packets:
        from scapy.all import IP, IPv6
        for pkt in packets:
            if pkt.haslayer(IP):
                src = str(pkt[IP].src)
                dst = str(pkt[IP].dst)
                unique_srcs.add(src)
                unique_dsts.add(dst)
                if not source_ip:
                    source_ip = src
                    destination_ip = dst
                    ip_ver = "IPv4"
            elif pkt.haslayer(IPv6):
                src = str(pkt[IPv6].src)
                dst = str(pkt[IPv6].dst)
                unique_srcs.add(src)
                unique_dsts.add(dst)
                if not source_ip:
                    source_ip = src
                    destination_ip = dst
                    ip_ver = "IPv6"

    if not source_ip and tshark_packets:
        for pkt in tshark_packets:
            layers = pkt.get("_source", {}).get("layers", {})
            if "ip" in layers:
                ip_layer = layers["ip"]
                src = ip_layer.get("ip.src")
                dst = ip_layer.get("ip.dst")
                if isinstance(src, list):
                    src = src[0]
                if isinstance(dst, list):
                    dst = dst[0]
                if src and dst:
                    src_str, dst_str = str(src), str(dst)
                    unique_srcs.add(src_str)
                    unique_dsts.add(dst_str)
                    if not source_ip:
                        source_ip = src_str
                        destination_ip = dst_str
                        ip_ver = "IPv4"
            elif "ipv6" in layers:
                ip_layer = layers["ipv6"]
                src = ip_layer.get("ipv6.src")
                dst = ip_layer.get("ipv6.dst")
                if isinstance(src, list):
                    src = src[0]
                if isinstance(dst, list):
                    dst = dst[0]
                if src and dst:
                    src_str, dst_str = str(src), str(dst)
                    unique_srcs.add(src_str)
                    unique_dsts.add(dst_str)
                    if not source_ip:
                        source_ip = src_str
                        destination_ip = dst_str
                        ip_ver = "IPv6"

    return source_ip, destination_ip, ip_ver, unique_srcs, unique_dsts


def _analyze_identity_payloads(
    packets: Optional[List[Any]] = None,
    tshark_packets: Optional[List[Dict[str, Any]]] = None,
    ike_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse IKE Identity Payloads ($ID_i$ / $ID_r$) and detect plaintext identity exposure.
    """
    identities_found = []
    plaintext_leak = False

    if packets:
        from scapy.all import ISAKMP
        for pkt in packets:
            if pkt.haslayer(ISAKMP):
                isakmp = pkt[ISAKMP]
                curr = isakmp.payload
                while curr and not isinstance(curr, (str, bytes)):
                    layer_name = curr.__class__.__name__
                    payload_type = getattr(curr, "payload_type", None)
                    if "ID" in layer_name or payload_type in (5, 35, 36):
                        id_type_num = getattr(curr, "id_type", getattr(curr, "IDtype", 1))
                        id_type_str = ID_TYPES.get(id_type_num, f"ID_TYPE_{id_type_num}")
                        load_val = getattr(curr, "load", getattr(curr, "id_data", b""))
                        if isinstance(load_val, bytes):
                            try:
                                val_str = load_val.decode("utf-8", errors="ignore").strip()
                            except Exception:
                                val_str = load_val.hex()
                        else:
                            val_str = str(load_val)

                        exch = getattr(isakmp, "exch_type", 0)
                        # IKEv1 Aggressive (4), Main Mode early exchange (2), IKE_SA_INIT (34)
                        is_unencrypted = exch in (2, 4, 34)
                        if is_unencrypted:
                            plaintext_leak = True

                        identities_found.append({
                            "type": id_type_str,
                            "value": val_str or "binary_identity_payload",
                            "encrypted": not is_unencrypted,
                            "risk": "HIGH" if is_unencrypted else "LOW"
                        })
                    curr = getattr(curr, "payload", None)

    if tshark_packets:
        for pkt in tshark_packets:
            layers = pkt.get("_source", {}).get("layers", {})
            ike_layer = layers.get("ike2") or layers.get("isakmp", {})
            for k, v in ike_layer.items():
                if any(term in k for term in ["id.type", "id_type", "payload.id"]):
                    id_str = str(v)
                    identities_found.append({
                        "type": id_str,
                        "value": "observed_via_tshark",
                        "encrypted": False,
                        "risk": "MEDIUM"
                    })
                    plaintext_leak = True

    return {
        "identities_found": identities_found,
        "plaintext_identity_leak": plaintext_leak,
        "identity_protection_status": "PLAINTEXT_EXPOSED" if plaintext_leak else "ENCRYPTED_OR_ABSENT",
        "exposed_identity_type": identities_found[0]["type"] if identities_found else None,
        "summary": (
            "Plaintext identity payload (e.g. FQDN / Email / IP) exposed in unencrypted exchange."
            if plaintext_leak
            else "No unencrypted identity payloads exposed in packet headers."
        )
    }


def _analyze_spi_correlation(
    ike_info: Dict[str, Any],
    esp_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate SPI correlation, session linkability, and persistent tracking vulnerability.
    """
    init_spi = ike_info.get("initiator_spi")
    resp_spi = ike_info.get("responder_spi")
    esp_spis = esp_info.get("observed_spis", [])

    all_spis = []
    if init_spi:
        all_spis.append(str(init_spi))
    if resp_spi and resp_spi != "0000000000000000":
        all_spis.append(str(resp_spi))
    for s in esp_spis:
        all_spis.append(str(s))

    spi_count = len(set(all_spis))

    linkability_risk = "LOW"
    if esp_spis:
        linkability_risk = "MEDIUM"
        if len(set(esp_spis)) == 1:
            # Single static ESP SPI across flow
            linkability_risk = "MEDIUM"

    return {
        "initiator_spi": init_spi,
        "responder_spi": resp_spi,
        "esp_spis": esp_spis,
        "total_unique_spis": spi_count,
        "spi_linkability_risk": linkability_risk,
        "session_tracking_vulnerability": len(esp_spis) > 0,
        "description": (
            "ESP SPI values are transmitted in cleartext (RFC 4303). "
            "Network eavesdroppers can track tunnel session flows across network topological changes using SPI headers."
            if esp_spis else "No cleartext ESP SPI tracking vulnerabilities detected."
        )
    }


def _analyze_transport_mode_exposure(mode: str, ip_ver: str) -> Dict[str, Any]:
    """
    Assess Transport Mode outer header exposure vs Tunnel Mode complete encapsulation.
    """
    is_transport = (str(mode).lower() == "transport")
    hdr_bytes = 40 if ip_ver == "IPv6" else 20

    if is_transport:
        return {
            "encapsulation_mode": "Transport",
            "inner_header_exposed": True,
            "exposed_metadata_bytes_per_pkt": hdr_bytes,
            "exposure_risk": "HIGH",
            "description": f"Transport Mode exposes original {ip_ver} source and destination IP addresses ({hdr_bytes} bytes per packet header) to intermediate routers and eavesdroppers."
        }
    else:
        return {
            "encapsulation_mode": mode if mode and mode != "unknown" else "Tunnel",
            "inner_header_exposed": False,
            "exposed_metadata_bytes_per_pkt": 0,
            "exposure_risk": "LOW",
            "description": f"Tunnel Mode encapsulates original internal IP headers inside a new outer {ip_ver} security envelope, hiding internal network topology."
        }


def analyze_metadata_exposure(
    packets: Optional[List[Any]] = None,
    tshark_packets: Optional[List[Dict[str, Any]]] = None,
    ike_info: Optional[Dict[str, Any]] = None,
    esp_info: Optional[Dict[str, Any]] = None,
    ipsec_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Perform comprehensive observable metadata exposure analysis on IPsec PCAP captures:
    1. Visible Endpoint IPs & Topological Leakage
    2. IKE Identity Payload Analysis ($ID_i$ / $ID_r$)
    3. SPI Correlation & Session Linkability Risk
    4. Transport Mode Header Exposure Analysis
    """
    ike_info = ike_info or {}
    esp_info = esp_info or {}
    ipsec_config = ipsec_config or {}

    source_ip, destination_ip, ip_ver, unique_srcs, unique_dsts = _extract_endpoint_ips(packets, tshark_packets)
    identity_res = _analyze_identity_payloads(packets, tshark_packets, ike_info)
    spi_res = _analyze_spi_correlation(ike_info, esp_info)

    mode = ipsec_config.get("mode", "unknown")
    transport_res = _analyze_transport_mode_exposure(mode, ip_ver)

    exposure_score = 0
    exposure_findings = []

    if identity_res.get("plaintext_identity_leak", False):
        exposure_score += 40
        exposure_findings.append({
            "finding_id": "IPSEC-META-001",
            "category": "Metadata Exposure",
            "severity": "HIGH",
            "title": "Plaintext IKE Identity Payload Exposed",
            "observed": f"Unencrypted {identity_res.get('exposed_identity_type', 'Identity Payload')} detected",
            "expected": "Encrypted Identity Payloads (IKEv2 IKE_AUTH or IKEv1 Encrypted Main Mode)",
            "recommendation": "Avoid IKEv1 Aggressive Mode or plaintext identity exchanges to prevent identity exposure."
        })

    if transport_res.get("exposure_risk") == "HIGH":
        exposure_score += 30
        exposure_findings.append({
            "finding_id": "IPSEC-META-002",
            "category": "Metadata Exposure",
            "severity": "MEDIUM",
            "title": "Transport Mode Exposes Internal Endpoint Topology",
            "observed": "Transport Mode Encapsulation",
            "expected": "Tunnel Mode Encapsulation",
            "recommendation": "Migrate from Transport Mode to Tunnel Mode to encapsulate original source and destination IP headers."
        })

    if spi_res.get("spi_linkability_risk") in ["HIGH", "MEDIUM"]:
        exposure_score += 15
        exposure_findings.append({
            "finding_id": "IPSEC-META-003",
            "category": "Metadata Exposure",
            "severity": "LOW",
            "title": "Static SPI Header Linkability / Session Tracking Risk",
            "observed": f"Observable ESP SPI(s): {', '.join(spi_res.get('esp_spis', [])) or 'Fixed SPIs'}",
            "expected": "Dynamic SA Rekeying & SPI Rotation",
            "recommendation": "Ensure frequent Security Association rekeying to prevent passive netflow session correlation."
        })

    exposure_rating = "LOW"
    if exposure_score >= 60:
        exposure_rating = "CRITICAL"
    elif exposure_score >= 40:
        exposure_rating = "HIGH"
    elif exposure_score >= 20:
        exposure_rating = "MEDIUM"

    return {
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "ip_version": ip_ver,
        "exposure_score": exposure_score,
        "exposure_rating": exposure_rating,
        "visible_endpoints": {
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "ip_version": ip_ver,
            "unique_source_ips": list(unique_srcs),
            "unique_destination_ips": list(unique_dsts),
            "outer_header_exposure": "FULL_IP_PAIR_VISIBLE" if (source_ip and destination_ip) else "LIMITED"
        },
        "identity_exposure": identity_res,
        "spi_correlation": spi_res,
        "transport_mode_exposure": transport_res,
        "exposure_findings": exposure_findings
    }
