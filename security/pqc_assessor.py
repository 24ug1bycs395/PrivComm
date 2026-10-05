"""Evidence-bounded post-quantum and crypto-agility assessment."""

import math
from typing import Any, Dict, List

NIST_ML_KEM_REFERENCE = "https://csrc.nist.gov/pubs/fips/203/final"
CNSA_2_REFERENCE = (
    "https://media.defense.gov/2022/Sep/07/2003071834/-1/-1/0/"
    "CSI_CNSA_2.0_ALGORITHMS_.PDF"
)
MOSCA_REFERENCE = "https://doi.org/10.1109/MSP.2018.3761723"

_CLASSICAL_DH_GROUPS = {
    "1", "2", "5", "14", "15", "16", "17", "18", "19", "20", "21",
    "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
    "MODP-1024", "MODP-2048", "MODP-3072", "MODP-4096",
    "ECP-256", "ECP-384", "CURVE25519", "CURVE448",
}


def _known(value: Any) -> bool:
    return value is not None and str(value).strip().lower() not in {"", "unknown", "none"}


def _assess_key_exchange(value: Any) -> Dict[str, Any]:
    if not _known(value):
        return {
            "status": "UNKNOWN",
            "observed": "unknown",
            "impact": "The capture or configuration does not expose a key-exchange algorithm.",
            "evidence": "No observable value",
        }
    group = str(value).upper()
    if group in _CLASSICAL_DH_GROUPS:
        return {
            "status": "CLASSICAL_VULNERABLE",
            "observed": group,
            "impact": "This is classical public-key cryptography and is not post-quantum secure.",
            "evidence": "Observed classical IKE key-exchange group",
        }
    if "ML-KEM" in group or "KYBER" in group:
        return {
            "status": "PQ_CANDIDATE_UNVERIFIED",
            "observed": group,
            "impact": "A PQ algorithm is named, but the capture alone does not establish correct implementation or successful hybrid negotiation.",
            "evidence": "Observed name only; interoperability and implementation validation are required",
        }
    return {
        "status": "UNKNOWN",
        "observed": group,
        "impact": "The observed key-exchange identifier cannot be classified by this assessor.",
        "evidence": "Unrecognized identifier",
    }


def _assess_symmetric_cipher(cipher: Any, key_length: Any) -> Dict[str, Any]:
    if not _known(cipher):
        return {
            "status": "UNKNOWN",
            "observed": "unknown",
            "impact": "The symmetric cipher is not observable.",
        }
    cipher_name = str(cipher).upper()
    bits = None
    if _known(key_length):
        try:
            bits = int(key_length)
        except (TypeError, ValueError):
            bits = None
    if bits is None:
        if "256" in cipher_name or "CHACHA20" in cipher_name:
            bits = 256
        elif "128" in cipher_name:
            bits = 128
    if bits == 256:
        status = "256_BIT_CLASSICAL"
        impact = "A 256-bit symmetric key is not a post-quantum algorithm; Grover-style search changes the security margin."
    elif bits is not None and bits < 256:
        status = "BELOW_256_BITS"
        impact = "The observed key size is below the 256-bit transition target; assess the required security margin."
    else:
        status = "UNKNOWN"
        impact = "The key length cannot be established from the observed cipher name."
    return {"status": status, "observed": cipher_name, "key_length_bits": bits, "impact": impact}


def evaluate_post_quantum_readiness(ipsec_info: Dict[str, Any]) -> Dict[str, Any]:
    """Assess only observed values; missing fields remain explicitly unknown."""
    key_exchange = _assess_key_exchange(ipsec_info.get("dh_group"))
    symmetric = _assess_symmetric_cipher(
        ipsec_info.get("encryption"), ipsec_info.get("key_length")
    )
    ike_version = ipsec_info.get("ike_version")

    if key_exchange["status"] == "CLASSICAL_VULNERABLE":
        overall = "CLASSICAL_KEY_EXCHANGE_OBSERVED"
    elif key_exchange["status"] == "PQ_CANDIDATE_UNVERIFIED":
        overall = "PQC_CANDIDATE_UNVERIFIED"
    else:
        overall = "INSUFFICIENT_EVIDENCE"

    timeline_values = [
        ipsec_info.get("data_shelf_life_years"),
        ipsec_info.get("migration_lead_time_years"),
        ipsec_info.get("estimated_crqc_years"),
    ]
    if all(_known(value) for value in timeline_values):
        try:
            shelf_life, migration, crqc_horizon = map(float, timeline_values)
        except (TypeError, ValueError):
            shelf_life = migration = crqc_horizon = -1.0
        valid_timeline = all(
            math.isfinite(value) and value >= 0
            for value in (shelf_life, migration, crqc_horizon)
        )
    else:
        valid_timeline = False

    if valid_timeline:
        mosca = {
            "status": "MIGRATION_WINDOW_EXCEEDS_HORIZON"
            if shelf_life + migration > crqc_horizon
            else "MIGRATION_WINDOW_WITHIN_HORIZON",
            "data_shelf_life_years": shelf_life,
            "migration_lead_time_years": migration,
            "estimated_crqc_years": crqc_horizon,
            "inequality": "data shelf life + migration lead time > estimated CRQC horizon",
            "source": MOSCA_REFERENCE,
            "source_model": "Mosca's x + y > z inequality; numeric inputs are caller-provided estimates.",
        }
    elif all(_known(value) for value in timeline_values):
        mosca = {
            "status": "INVALID_INPUT",
            "required_inputs": [
                "finite non-negative data_shelf_life_years",
                "finite non-negative migration_lead_time_years",
                "finite non-negative estimated_crqc_years",
            ],
            "source": MOSCA_REFERENCE,
        }
    else:
        mosca = {
            "status": "NOT_ASSESSED",
            "required_inputs": [
                "data_shelf_life_years",
                "migration_lead_time_years",
                "estimated_crqc_years",
            ],
            "source": MOSCA_REFERENCE,
            "source_model": "Mosca's x + y > z inequality; the assessor does not invent a CRQC arrival date.",
        }

    pqc_candidate = {
        "status": key_exchange["status"],
        "observed": key_exchange["observed"],
        "source": NIST_ML_KEM_REFERENCE,
        "note": "The NIST reference defines ML-KEM; an observed name is not proof of conformance.",
    }
    checks: List[Dict[str, Any]] = [
        {
            "control": "Key Exchange Quantum Resilience",
            **key_exchange,
            "source": NIST_ML_KEM_REFERENCE,
        },
        {
            "control": "Symmetric Cipher Quantum Margin",
            **symmetric,
        },
        {
            "control": "Negotiated Post-Quantum Key Exchange",
            "status": "NOT_VERIFIED",
            "observed": ike_version if _known(ike_version) else "unknown",
            "impact": "IKE version alone does not prove that a hybrid or post-quantum key exchange was configured or negotiated.",
        },
        {
            "control": "CNSA 2.0 Profile",
            "status": "NOT_ASSESSED",
            "observed": "No explicit CNSA 2.0 profile or implementation evidence supplied",
            "profile": "Commercial National Security Algorithm Suite 2.0",
            "profile_version": "2.0",
            "published_date": "2022-09-07",
            "applicability": "U.S. National Security Systems; applicability outside NSS is not assumed.",
            "source": CNSA_2_REFERENCE,
        },
    ]

    return {
        "pqc_status": overall,
        "readiness_score": None,
        "key_exchange_family": key_exchange["observed"],
        "symmetric_quantum_status": symmetric["status"],
        "crypto_agility_rating": "UNVERIFIED",
        "pqc_candidate": pqc_candidate,
        "cnsa_2": {
            "status": "NOT_ASSESSED",
            "profile_version": "2.0",
            "published_date": "2022-09-07",
            "applicability": "U.S. National Security Systems; applicability outside NSS is not assumed.",
            "source": CNSA_2_REFERENCE,
            "note": "Algorithm observations do not establish CNSA 2.0 profile compliance or deployment readiness.",
        },
        "mosca_timeline": mosca,
        "pqc_checks": checks,
    }
