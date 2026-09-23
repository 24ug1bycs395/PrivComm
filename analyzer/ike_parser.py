import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Standard IKEv2 Transform Mappings (RFC 7296)
ENCRYPTION_TRANSFORMS = {
    1: "DES",
    2: "3DES",
    3: "CAST",
    4: "BLOWFISH",
    12: "AES-CBC",
    13: "AES-CTR",
    18: "AES-CCM-16",
    19: "AES-GCM-8",
    20: "AES-GCM-16"
}

PRF_TRANSFORMS = {
    1: "HMAC-MD5",
    2: "HMAC-SHA1",
    4: "HMAC-SHA2-256",
    5: "HMAC-SHA2-384",
    6: "HMAC-SHA2-512",
    7: "AES128-XCBC"
}

INTEGRITY_TRANSFORMS = {
    0: "AEAD",
    1: "HMAC-MD5-96",
    2: "HMAC-SHA1-96",
    12: "HMAC-SHA2-256",
    13: "HMAC-SHA2-384",
    14: "HMAC-SHA2-512"
}

DH_GROUP_TRANSFORMS = {
    1: 1,    # 768-bit MODP
    2: 2,    # 1024-bit MODP
    5: 5,    # 1536-bit MODP
    14: 14,  # 2048-bit MODP
    15: 15,  # 3072-bit MODP
    16: 16,  # 4096-bit MODP
    19: 19,  # 256-bit ECP (Group 19)
    20: 20,  # 384-bit ECP (Group 20)
    21: 21,  # 521-bit ECP (Group 21)
    28: 28   # Curve25519
}


def parse_ike_scapy(packets: List[Any]) -> Dict[str, Any]:
    """Parse IKE packets using Scapy layer objects."""
    result = {
        "ike_detected": False,
        "ike_version": "unknown",
        "initiator_spi": None,
        "responder_spi": None,
        "encryption": "unknown",
        "key_length": None,
        "integrity": "unknown",
        "prf": "unknown",
        "dh_group": "unknown",
        "exchange_type": "unknown"
    }

    from scapy.all import ISAKMP

    for pkt in packets:
        if pkt.haslayer(ISAKMP):
            isakmp = pkt[ISAKMP]
            result["ike_detected"] = True

            ver_byte = getattr(isakmp, "version", 0x20)
            major = (ver_byte >> 4) & 0x0F
            if major == 2:
                result["ike_version"] = "IKEv2"
            elif major == 1:
                result["ike_version"] = "IKEv1"

            init_c = getattr(isakmp, "init_cookie", None)
            if init_c is not None:
                result["initiator_spi"] = init_c.hex() if isinstance(init_c, bytes) else f"{init_c:016x}"

            resp_c = getattr(isakmp, "resp_cookie", None)
            if resp_c is not None:
                result["responder_spi"] = resp_c.hex() if isinstance(resp_c, bytes) else f"{resp_c:016x}"

            exch_type = getattr(isakmp, "exch_type", None)
            if exch_type == 34:
                result["exchange_type"] = "IKE_SA_INIT"
            elif exch_type == 35:
                result["exchange_type"] = "IKE_AUTH"

            # Parse payloads for SA proposals
            curr = isakmp.payload
            while curr and not isinstance(curr, str) and not isinstance(curr, bytes):
                load_bytes = getattr(curr, "load", b"")
                if load_bytes:
                    _parse_transform_load(load_bytes, result)

                curr = curr.payload

    return result


def _parse_transform_load(load_bytes: bytes, result: Dict[str, Any]):
    """Extract transforms from raw IKE payload bytes adhering strictly to RFC 7296 structure."""
    if len(load_bytes) < 8:
        return

    offset = 0
    # Skip Proposal header if load starts with proposal attributes (8 bytes)
    # Typical proposal header: 4 bytes proposal header + 4 bytes protocol details
    if load_bytes[0:2] == b'\x00\x00' or load_bytes[0] == 0:
        if len(load_bytes) >= 8 and load_bytes[2] == 0 and load_bytes[3] in (0, 36, 40):
            offset = 8

    while offset + 8 <= len(load_bytes):
        tf_len = int.from_bytes(load_bytes[offset+2:offset+4], byteorder='big')
        if tf_len < 8 or offset + tf_len > len(load_bytes):
            offset += 4
            continue

        tf_type = load_bytes[offset+4]
        tf_id = int.from_bytes(load_bytes[offset+6:offset+8], byteorder='big')

        # Check for Key Length attribute (0x800e)
        key_len = None
        if tf_len >= 12 and load_bytes[offset+8:offset+10] == b'\x80\x0e':
            key_len = int.from_bytes(load_bytes[offset+10:offset+12], byteorder='big')

        if tf_type == 1: # Encryption
            enc_name = ENCRYPTION_TRANSFORMS.get(tf_id, f"ENCR_{tf_id}")
            if key_len and "AES" in enc_name:
                result["encryption"] = f"AES-{key_len}-GCM" if "GCM" in enc_name else f"AES-{key_len}-CBC"
                result["key_length"] = key_len
            else:
                result["encryption"] = enc_name

        elif tf_type == 2: # PRF
            result["prf"] = PRF_TRANSFORMS.get(tf_id, f"HMAC-SHA2-384" if tf_id == 5 else f"PRF_{tf_id}")

        elif tf_type == 3: # Integrity
            result["integrity"] = INTEGRITY_TRANSFORMS.get(tf_id, f"INTEG_{tf_id}")

        elif tf_type == 4: # DH Group
            if tf_id in DH_GROUP_TRANSFORMS:
                result["dh_group"] = DH_GROUP_TRANSFORMS[tf_id]
            else:
                result["dh_group"] = tf_id

        offset += tf_len


def parse_ike_tshark_json(tshark_packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse IKE parameters from TShark JSON output."""
    result = {
        "ike_detected": False,
        "ike_version": "unknown",
        "initiator_spi": None,
        "responder_spi": None,
        "encryption": "unknown",
        "key_length": None,
        "integrity": "unknown",
        "prf": "unknown",
        "dh_group": "unknown",
        "exchange_type": "unknown"
    }

    for pkt in tshark_packets:
        layers = pkt.get("_source", {}).get("layers", {})
        if "ike2" in layers or "isakmp" in layers:
            result["ike_detected"] = True
            ike_layer = layers.get("ike2") or layers.get("isakmp", {})

            if "ike2" in layers:
                result["ike_version"] = "IKEv2"
            elif "isakmp" in layers:
                result["ike_version"] = "IKEv1"

            if "ike2.ispi" in ike_layer:
                result["initiator_spi"] = str(ike_layer["ike2.ispi"])
            if "ike2.rspi" in ike_layer:
                result["responder_spi"] = str(ike_layer["ike2.rspi"])

            for key, val in ike_layer.items():
                if "transform.encr" in key or "transform.type.encr" in key:
                    result["encryption"] = str(val)
                elif "transform.dh" in key or "transform.type.dh" in key:
                    try:
                        result["dh_group"] = int(val)
                    except ValueError:
                        result["dh_group"] = str(val)
                elif "transform.prf" in key:
                    result["prf"] = str(val)
                elif "transform.auth" in key or "transform.integ" in key:
                    result["integrity"] = str(val)

    return result
