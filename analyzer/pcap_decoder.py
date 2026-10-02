"""Small dependency-free PCAP/PCAPNG decoder for IPsec-specific packets."""

import os
import socket
import struct
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IKEPacket:
    """Parsed IKE packet metadata."""

    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    ike_version: str
    exchange_type: int
    exchange_name: str
    initiator_spi: str
    responder_spi: str
    message_id: int
    is_initiator: bool
    is_response: bool
    payloads: list[str]
    proposals: list[dict[str, Any]]
    notifies: list[dict[str, Any]]
    raw_hex: str


@dataclass
class ESPPacket:
    """Parsed ESP packet metadata."""

    timestamp: float
    src_ip: str
    dst_ip: str
    spi: str
    sequence_number: int
    payload_length: int


@dataclass
class PCAPDecodeResult:
    """Result of decoding one capture file."""

    file_format: str
    link_type: int
    packet_count: int
    ike_packets: list[IKEPacket] = field(default_factory=list)
    esp_packets: list[ESPPacket] = field(default_factory=list)
    ike_versions_seen: set[str] = field(default_factory=set)
    unique_spis: set[str] = field(default_factory=set)
    parse_errors: list[str] = field(default_factory=list)


def _exchange_name(value: int) -> str:
    names = {34: "IKE_SA_INIT", 35: "IKE_AUTH", 36: "CREATE_CHILD_SA", 37: "INFORMATIONAL"}
    return names.get(value, "UNKNOWN")


def _read_capture_records(path: str) -> tuple[str, int, list[tuple[float, bytes]]]:
    with open(path, "rb") as handle:
        data = handle.read()
    if len(data) < 4:
        raise ValueError("Capture is too short to identify")
    magic = data[:4]
    pcap_magics = (
        b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4",
        b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d",
    )
    if magic in pcap_magics:
        return _read_pcap(data)
    if magic == b"\x0a\x0d\x0d\x0a":
        return _read_pcapng(data)
    raise ValueError(f"Unrecognized capture magic: {magic.hex()}")


def _read_pcap(data: bytes) -> tuple[str, int, list[tuple[float, bytes]]]:
    if len(data) < 24:
        raise ValueError("PCAP global header is incomplete")
    little = data[:4] in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1")
    endian = "<" if little else ">"
    _, _, _, _, _, _, link_type = struct.unpack_from(f"{endian}IHHIIII", data, 0)
    records: list[tuple[float, bytes]] = []
    offset = 24
    while offset + 16 <= len(data):
        seconds, fraction, captured, _ = struct.unpack_from(f"{endian}IIII", data, offset)
        offset += 16
        if offset + captured > len(data):
            raise ValueError("PCAP record extends beyond file")
        records.append((seconds + fraction / 1_000_000, data[offset:offset + captured]))
        offset += captured
    return "PCAP", link_type, records


def _read_pcapng(data: bytes) -> tuple[str, int, list[tuple[float, bytes]]]:
    offset = 0
    link_type = 1
    interfaces: dict[int, tuple[int, int]] = {}
    records: list[tuple[float, bytes]] = []
    endian = "<"
    while offset + 12 <= len(data):
        block_type = struct.unpack_from(f"{endian}I", data, offset)[0]
        block_length = struct.unpack_from(f"{endian}I", data, offset + 4)[0]
        if block_length < 12 or offset + block_length > len(data):
            raise ValueError("PCAPNG block is malformed")
        block = data[offset:offset + block_length]
        if block_type == 0x0A0D0D0A:
            byte_order = block[8:12]
            if byte_order == b"\x1a\x2b\x3c\x4d":
                endian = ">"
            elif byte_order == b"\x4d\x3c\x2b\x1a":
                endian = "<"
        elif block_type == 1 and len(block) >= 20:
            interface_id = len(interfaces)
            link_type, _, snaplen = struct.unpack_from(f"{endian}HHI", block, 8)
            interfaces[interface_id] = (link_type, snaplen)
        elif block_type == 6 and len(block) >= 32:
            interface_id, ts_high, ts_low, captured, _ = struct.unpack_from(
                f"{endian}IIIII", block, 8
            )
            packet_start = 28
            packet = block[packet_start:packet_start + captured]
            timestamp = ((ts_high << 32) | ts_low) / 1_000_000
            records.append((timestamp, packet))
            if interface_id in interfaces:
                link_type = interfaces[interface_id][0]
        elif block_type == 3 and len(block) >= 16:
            original_length = struct.unpack_from(f"{endian}I", block, 8)[0]
            packet = block[12:block_length - 4]
            records.append((0.0, packet[:original_length]))
        offset += block_length
    return "PCAPNG", link_type, records


def _ipv4(packet: bytes) -> tuple[str, str, int, bytes] | None:
    if len(packet) < 20 or packet[0] >> 4 != 4:
        return None
    header_length = (packet[0] & 0x0F) * 4
    if header_length < 20 or len(packet) < header_length:
        return None
    return (
        socket.inet_ntoa(packet[12:16]),
        socket.inet_ntoa(packet[16:20]),
        packet[9],
        packet[header_length:],
    )


def _ipv6(packet: bytes) -> tuple[str, str, int, bytes] | None:
    if len(packet) < 40 or packet[0] >> 4 != 6:
        return None
    source = socket.inet_ntop(socket.AF_INET6, packet[8:24])
    destination = socket.inet_ntop(socket.AF_INET6, packet[24:40])
    next_header = packet[6]
    offset = 40
    while next_header in (0, 43, 44, 60) and offset + 8 <= len(packet):
        if next_header == 44:
            next_header = packet[offset]
            offset += 8
        else:
            next_header = packet[offset]
            offset += (packet[offset + 1] + 1) * 8
    return source, destination, next_header, packet[offset:]


def _network_packet(raw: bytes, link_type: int) -> tuple[str, str, int, bytes] | None:
    if link_type == 1:
        if len(raw) < 14:
            return None
        ethertype = struct.unpack("!H", raw[12:14])[0]
        if ethertype == 0x0800:
            return _ipv4(raw[14:])
        if ethertype == 0x86DD:
            return _ipv6(raw[14:])
        return None
    if link_type == 101:
        version = raw[0] >> 4 if raw else 0
        return _ipv4(raw) if version == 4 else _ipv6(raw) if version == 6 else None
    return None


def _parse_sa(data: bytes) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    offset = 0
    while offset + 8 <= len(data):
        last, _, length, number, protocol, spi_size, transform_count = struct.unpack_from(
            "!BBBBBBH", data, offset
        )
        if length < 8 or offset + length > len(data):
            break
        transform_offset = offset + 8 + spi_size
        proposal = {"number": number, "protocol_id": protocol, "transforms": []}
        for _ in range(transform_count):
            if transform_offset + 8 > offset + length:
                break
            _, _, transform_length, transform_type, _, transform_id = struct.unpack_from(
                "!BBHBBH", data, transform_offset
            )
            if transform_length < 8 or transform_offset + transform_length > offset + length:
                break
            transform: dict[str, Any] = {"type": transform_type, "id": transform_id}
            attrs = data[transform_offset + 8:transform_offset + transform_length]
            if len(attrs) >= 4:
                attr_type = struct.unpack("!H", attrs[:2])[0]
                if attr_type == 0x800E:
                    transform["key_length"] = struct.unpack("!H", attrs[2:4])[0]
            proposal["transforms"].append(transform)
            transform_offset += transform_length
        proposals.append(proposal)
        offset += length
        if last == 0:
            break
    return proposals


def _parse_ike(
    payload: bytes,
    timestamp: float,
    source: str,
    destination: str,
    source_port: int,
    destination_port: int,
) -> IKEPacket | None:
    if len(payload) < 28:
        return None
    initiator_spi, responder_spi = payload[:8], payload[8:16]
    next_payload, version, exchange_type, flags, message_id, _ = struct.unpack_from(
        "!BBBBII", payload, 16
    )
    payload_names = {
        33: "SA", 34: "KE", 35: "IDi", 36: "IDr", 37: "CERT",
        38: "CERTREQ", 39: "AUTH", 40: "Nonce", 41: "Notify", 43: "Vendor ID",
    }
    proposals: list[dict[str, Any]] = []
    notifies: list[dict[str, Any]] = []
    names: list[str] = []
    offset = 28
    while next_payload and offset + 4 <= len(payload):
        current = next_payload
        next_payload, _, length = struct.unpack_from("!BBH", payload, offset)
        if length < 4 or offset + length > len(payload):
            break
        data = payload[offset + 4:offset + length]
        names.append(payload_names.get(current, f"PAYLOAD_{current}"))
        if current == 33:
            proposals.extend(_parse_sa(data))
        elif current == 41 and len(data) >= 4:
            notify_type = struct.unpack("!H", data[2:4])[0]
            notify_names = {
                16388: "NAT_DETECTION_SOURCE_IP",
                16389: "NAT_DETECTION_DESTINATION_IP",
                16401: "COOKIE",
            }
            notifies.append({
                "notify_type": notify_type,
                "notify_name": notify_names.get(notify_type, "UNKNOWN"),
                "data_hex": data[4:].hex(),
            })
        offset += length
    major = version >> 4
    version_name = "IKEv2" if major == 2 else "IKEv1" if major == 1 else "unknown"
    return IKEPacket(
        timestamp, source, destination, source_port, destination_port, version_name,
        exchange_type, _exchange_name(exchange_type), initiator_spi.hex(),
        responder_spi.hex(), message_id, not bool(flags & 0x20), bool(flags & 0x20),
        names, proposals, notifies, payload.hex(),
    )


def _parse_record(timestamp: float, raw: bytes, link_type: int, result: PCAPDecodeResult) -> None:
    network = _network_packet(raw, link_type)
    if not network:
        return
    source, destination, protocol, payload = network
    if protocol == 50 and len(payload) >= 8:
        spi, sequence = struct.unpack("!II", payload[:8])
        ip_packet = raw[14:] if link_type == 1 and len(raw) >= 14 else raw
        result.esp_packets.append(ESPPacket(
            timestamp, source, destination, f"0x{spi:08x}", sequence, len(ip_packet)
        ))
        result.unique_spis.add(f"0x{spi:08x}")
    elif protocol == 17 and len(payload) >= 8:
        source_port, destination_port, length, _ = struct.unpack("!HHHH", payload[:8])
        body = payload[8:8 + max(0, length - 8)]
        if source_port in (500, 4500) or destination_port in (500, 4500):
            packet = _parse_ike(body, timestamp, source, destination, source_port, destination_port)
            if packet:
                result.ike_packets.append(packet)
                result.ike_versions_seen.add(packet.ike_version)
                result.unique_spis.update((packet.initiator_spi, packet.responder_spi))


def decode_pcap(path: str) -> PCAPDecodeResult:
    """Decode PCAP or PCAPNG and return IPsec packet metadata."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    file_format, link_type, records = _read_capture_records(path)
    result = PCAPDecodeResult(file_format, link_type, len(records))
    for timestamp, raw in records:
        try:
            _parse_record(timestamp, raw, link_type, result)
        except (IndexError, OSError, struct.error, ValueError) as exc:
            result.parse_errors.append(str(exc))
    return result
