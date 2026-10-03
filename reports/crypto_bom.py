"""Build a capture-backed cryptographic inventory without inferring unknowns."""

from datetime import datetime, timezone
from typing import Any, Dict, List


def _known(value: Any) -> bool:
    return value is not None and str(value).strip().lower() not in {"", "unknown", "none"}


def build_crypto_bom(
    ipsec: Dict[str, Any],
    capture_sha256: str | None,
    packet_evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:
    components = []
    known_algorithms = (
        ("ike_version", "protocol", "IKE protocol"),
        ("encryption", "symmetric-encryption", "Encryption algorithm"),
        ("integrity", "integrity", "Integrity algorithm"),
        ("prf", "key-derivation", "Pseudorandom function"),
        ("dh_group", "key-exchange", "IKE key-exchange group"),
    )
    for field, component_type, description in known_algorithms:
        value = ipsec.get(field)
        if not _known(value):
            continue
        component_evidence = []
        for packet in packet_evidence:
            packet_fields = packet.get("fields", {})
            if field == "ike_version" and "ike_version" in packet_fields:
                component_evidence.append({
                    "frame_number": packet["frame_number"],
                    "capture_byte_offset": packet_fields["ike_version"]["capture_byte_offset"],
                    "capture_byte_length": packet_fields["ike_version"]["capture_byte_length"],
                })
            elif field == "dh_group" and packet.get("protocol") == "IKE":
                component_evidence.append({
                    "frame_number": packet["frame_number"],
                    "capture_byte_offset": packet["capture_byte_offset"],
                    "capture_byte_length": packet["capture_byte_length"],
                    "evidence_scope": "IKE message; group identity is decoded from its observable proposal",
                })
            elif field in {"encryption", "integrity", "prf"} and packet.get("protocol") == "IKE":
                component_evidence.append({
                    "frame_number": packet["frame_number"],
                    "capture_byte_offset": packet["capture_byte_offset"],
                    "capture_byte_length": packet["capture_byte_length"],
                    "evidence_scope": "IKE message; algorithm identified from decoded proposal",
                })
        components.append({
            "type": component_type,
            "name": str(value),
            "source_field": field,
            "description": description,
            "evidence": component_evidence,
            "evidence_status": "observed" if component_evidence else "parsed_from_configuration",
        })

    unresolved = [
        {
            "field": field,
            "status": "unknown",
            "reason": "No value was available in the analyzed configuration or capture.",
        }
        for field in ("ike_version", "encryption", "integrity", "prf", "dh_group")
        if not _known(ipsec.get(field))
    ]
    return {
        "bom_format": "PrivComm Crypto Bill of Materials",
        "schema_version": "privcomm.cbom.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capture": {"sha256": capture_sha256},
        "components": components,
        "unresolved": unresolved,
        "limitations": [
            "A packet reference proves only the bytes and fields at that location; it does not prove endpoint configuration or implementation correctness.",
            "Encrypted IKE_AUTH exchanges and unobserved rekeys may conceal negotiated or configured values.",
            "This is the PrivComm CBOM schema, not a claim of CycloneDX schema conformance.",
        ],
    }
