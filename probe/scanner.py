"""Minimal standard-library IKE_SA_INIT probe with bounded consent-gated I/O."""

import logging
import os
import socket
import struct
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

NOTIFY_COOKIE = 16401
NOTIFY_NAT_SOURCE = 16388
NOTIFY_NAT_DESTINATION = 16389


@dataclass
class ProbeResult:
    """Serializable result of one IKE probe attempt."""

    target_ip: str
    target_port: int
    reachable: bool = False
    ike_version: str = "unknown"
    initiator_spi: str = ""
    responder_spi: str = ""
    proposed_transforms: list[dict[str, Any]] | None = None
    vendor_ids: list[str] | None = None
    nat_detected: bool = False
    cookie_required: bool = False
    round_trip_ms: float = 0.0
    error: str | None = None
    raw_response_hex: str = ""
    probed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


def _transform_payload(
    transform_type: int, transform_id: int, key_length: int | None = None
) -> bytes:
    attrs = b""
    if key_length is not None:
        attrs = struct.pack("!HH", 0x800E, key_length)
    length = 8 + len(attrs)
    return struct.pack("!BBHBBH", 0, 0, length, transform_type, 0, transform_id) + attrs


def _proposal(number: int, transforms: list[bytes]) -> bytes:
    body = b"".join(transforms)
    header = struct.pack(
        "!BBHBBBB", 0 if number == 2 else 2, 0, 8 + len(body), number, 1, 0, len(transforms)
    )
    return header + body


def _sa_payload() -> bytes:
    strong = _proposal(1, [
        _transform_payload(1, 20, 256),
        _transform_payload(2, 5),
        _transform_payload(3, 13),
        _transform_payload(4, 20),
    ])
    weak = _proposal(2, [
        _transform_payload(1, 3),
        _transform_payload(2, 1),
        _transform_payload(3, 1),
        _transform_payload(4, 2),
    ])
    data = strong + weak
    return struct.pack("!BBH", 0, 0, 4 + len(data)) + data


def _nonce_payload() -> bytes:
    nonce = os.urandom(32)
    return struct.pack("!BBH", 0, 0, 4 + len(nonce)) + nonce


def _ke_payload() -> bytes:
    """Build a zero-filled DH group 14 KE payload for SA_INIT negotiation."""
    key_exchange = struct.pack("!HH", 14, 0) + b"\x00" * 256
    return struct.pack("!BBH", 40, 0, 4 + len(key_exchange)) + key_exchange


def _build_packet(initiator_spi: bytes, cookie: bytes | None = None) -> bytes:
    sa_payload = _sa_payload()
    sa_payload = bytes([41 if cookie else 34, 0, 0, 0]) + sa_payload[4:]
    payloads = sa_payload
    if cookie:
        cookie_payload = struct.pack("!BBH", 34, 0, 4 + len(cookie)) + cookie
        payloads += cookie_payload
    payloads += _ke_payload() + _nonce_payload()
    body = payloads
    header = initiator_spi + b"\x00" * 8 + bytes([33, 0x20, 34, 0x08])
    header += struct.pack("!II", 0, 28 + len(body))
    return header + body


def _parse_notify(data: bytes) -> tuple[int | None, bytes]:
    if len(data) < 4:
        return None, b""
    return struct.unpack("!H", data[2:4])[0], data[4:]


def _parse_sa(data: bytes) -> list[dict[str, Any]]:
    transforms: list[dict[str, Any]] = []
    offset = 0
    while offset + 8 <= len(data):
        length = struct.unpack("!H", data[offset + 2:offset + 4])[0]
        if length < 8 or offset + length > len(data):
            break
        transform_type = data[offset + 4]
        transform_id = struct.unpack("!H", data[offset + 6:offset + 8])[0]
        item: dict[str, Any] = {"type": transform_type, "id": transform_id}
        names = {
            1: {3: "3DES", 20: "AES-GCM"},
            2: {1: "HMAC-MD5", 5: "PRF-HMAC-SHA384"},
            3: {1: "HMAC-MD5", 13: "HMAC-SHA2-384"},
            4: {2: "DH-2", 20: "ECP-384"},
        }
        item["name"] = names.get(transform_type, {}).get(transform_id, f"TRANSFORM_{transform_id}")
        attrs = data[offset + 8:offset + length]
        if len(attrs) >= 4 and struct.unpack("!H", attrs[:2])[0] == 0x800E:
            item["key_length"] = struct.unpack("!H", attrs[2:4])[0]
        transforms.append(item)
        offset += length
    return transforms


def _parse_response(packet: bytes) -> dict[str, Any]:
    if len(packet) < 28:
        raise ValueError("IKE response is shorter than the 28-byte header")
    version = packet[17]
    result: dict[str, Any] = {
        "ike_version": (
            "IKEv2" if version >> 4 == 2 else "IKEv1" if version >> 4 == 1 else "unknown"
        ),
        "initiator_spi": packet[:8].hex(),
        "responder_spi": packet[8:16].hex(),
        "transforms": [],
        "vendor_ids": [],
        "cookie": None,
        "nat": False,
    }
    next_payload = packet[16]
    offset = 28
    while next_payload and offset + 4 <= len(packet):
        current = next_payload
        next_payload = packet[offset]
        length = struct.unpack("!H", packet[offset + 2:offset + 4])[0]
        if length < 4 or offset + length > len(packet):
            break
        data = packet[offset + 4:offset + length]
        if current == 33:
            result["transforms"].extend(_parse_sa(data))
        elif current == 41:
            notify_type, notify_data = _parse_notify(data)
            if notify_type == NOTIFY_COOKIE:
                result["cookie"] = notify_data
            if notify_type in (NOTIFY_NAT_SOURCE, NOTIFY_NAT_DESTINATION):
                result["nat"] = True
        elif current == 43:
            result["vendor_ids"].append(data.hex())
        offset += length
    return result


def probe(
    target_ip: str, port: int = 500, timeout_s: float = 5.0, use_ikev2: bool = True
) -> ProbeResult:
    """Send one minimal IKE_SA_INIT packet and parse its response."""
    started_at = datetime.now(timezone.utc).isoformat()
    result = ProbeResult(
        target_ip, port, proposed_transforms=[], vendor_ids=[], probed_at=started_at
    )
    if port not in (500, 4500):
        result.error = "IKE probe port must be 500 or 4500."
        return result
    spi = os.urandom(8)
    packet = _build_packet(spi)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout_s)
            logger.debug("Sending IKE probe to %s:%s (%d bytes)", target_ip, port, len(packet))
            sent_at = time.perf_counter()
            sock.sendto(packet, (target_ip, port))
            response, _ = sock.recvfrom(65535)
            result.round_trip_ms = round((time.perf_counter() - sent_at) * 1000, 3)
            logger.debug(
                "Received IKE probe response from %s:%s (%d bytes)",
                target_ip,
                port,
                len(response),
            )
            parsed = _parse_response(response)
            if parsed["cookie"]:
                result.cookie_required = True
                retry = _build_packet(spi, parsed["cookie"])
                logger.debug("Sending cookie-bearing IKE probe to %s:%s", target_ip, port)
                sock.sendto(retry, (target_ip, port))
                response, _ = sock.recvfrom(65535)
                parsed = _parse_response(response)
            result.reachable = True
            result.ike_version = parsed["ike_version"]
            result.initiator_spi = parsed["initiator_spi"]
            result.responder_spi = parsed["responder_spi"]
            result.proposed_transforms = parsed["transforms"]
            result.vendor_ids = parsed["vendor_ids"]
            result.nat_detected = parsed["nat"]
            result.raw_response_hex = response.hex()
    except socket.timeout:
        result.error = f"Probe timed out after {timeout_s} seconds."
    except OSError as exc:
        result.error = str(exc)
    return result


class IKEProbeScanner:
    """Compatibility wrapper exposing the probe function as a scanner class."""

    @staticmethod
    def probe(
        target_ip: str, port: int = 500, timeout_s: float = 5.0, use_ikev2: bool = True
    ) -> ProbeResult:
        """Run one IKE probe."""
        return probe(target_ip, port, timeout_s, use_ikev2)
