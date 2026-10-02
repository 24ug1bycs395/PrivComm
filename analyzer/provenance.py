"""Data provenance labels for analysis results.

The labels intentionally describe how a value was obtained, not how confident
the value appears.  This prevents an ML confidence score from being confused
with direct wire evidence.
"""

from typing import Any, Dict

OBSERVED = "OBSERVED"
PARSED = "PARSED"
INFERRED = "INFERRED"
UNKNOWN = "UNKNOWN"
PROVENANCE_LEVELS = frozenset({OBSERVED, PARSED, INFERRED, UNKNOWN})


def _known(value: Any) -> bool:
    return value is not None and value != "" and str(value).lower() != "unknown"


def build_data_provenance(
    *,
    ingest_result: Dict[str, Any],
    ipsec: Dict[str, Any],
    traffic_classification: Dict[str, Any] | None,
    behavioral_anomaly: Dict[str, Any] | None,
    metadata_exposure: Dict[str, Any] | None,
    rfc4303_elimination: Dict[str, Any] | None,
) -> Dict[str, str]:
    """Return a provenance label for every public analysis field."""

    successful_parse = ingest_result.get("status") == "success"
    provenance = {
        "ipsec_detected": OBSERVED if successful_parse else UNKNOWN,
        "ike_version": PARSED if _known(ipsec.get("ike_version")) else UNKNOWN,
        "esp_detected": OBSERVED if successful_parse else UNKNOWN,
        "ah_detected": OBSERVED if successful_parse else UNKNOWN,
        "mode": INFERRED if _known(ipsec.get("mode")) else UNKNOWN,
        "mode_confidence": INFERRED if _known(ipsec.get("mode_confidence")) else UNKNOWN,
        "encryption": PARSED if _known(ipsec.get("encryption")) else UNKNOWN,
        "integrity": PARSED if _known(ipsec.get("integrity")) else UNKNOWN,
        "dh_group": PARSED if _known(ipsec.get("dh_group")) else UNKNOWN,
        "pfs": UNKNOWN,
        "replay_protection": UNKNOWN,
        "ip_version": OBSERVED if _known(ingest_result.get("ip_version")) else UNKNOWN,
        "source_ip": OBSERVED if _known(ingest_result.get("source_ip")) else UNKNOWN,
        "destination_ip": OBSERVED if _known(ingest_result.get("destination_ip")) else UNKNOWN,
        "traffic_classification": (
            INFERRED if traffic_classification and traffic_classification.get("status") == "success" else UNKNOWN
        ),
        "behavioral_anomaly": INFERRED if behavioral_anomaly else UNKNOWN,
        "metadata_exposure": OBSERVED if metadata_exposure else UNKNOWN,
        "security_assessment": INFERRED,
        "explainability": INFERRED,
        "rfc4303_elimination": INFERRED if rfc4303_elimination else UNKNOWN,
    }

    # RFC 4303 arithmetic is an inference over observed packet lengths.  Make
    # that evidence visible instead of presenting it as direct cipher parsing.
    if ipsec.get("encryption_provenance") == "rfc4303_arithmetic":
        provenance["encryption"] = INFERRED

    return provenance
