"""
Post-Quantum Cryptographic Readiness & Crypto-Agility Assessment Engine.

Evaluates IPsec VPN configurations for vulnerability to quantum computing threats
(Shor's Algorithm / Store-Now-Decrypt-Later SNDL attacks), assesses Crypto-Agility rating,
and checks for IKEv2 Post-Quantum Hybrid Key Exchange readiness (RFC 8784 / ML-KEM Kyber).
"""

from typing import Dict, Any, List


def evaluate_post_quantum_readiness(ipsec_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates observed IPsec configuration for Post-Quantum readiness and Crypto-Agility.
    """
    dh_group = str(ipsec_info.get("dh_group", "19")).upper()
    enc_cipher = str(ipsec_info.get("encryption", "AES-256-GCM")).upper()
    ike_version = str(ipsec_info.get("ike_version", "IKEv2")).upper()
    pfs_enabled = True if ipsec_info.get("pfs") in [True, "enforced", "yes"] else False

    pqc_checks: List[Dict[str, Any]] = []

    # 1. Asymmetric Key Exchange Quantum Threat Assessment (Shor's Algorithm)
    if dh_group in ["1", "2", "5", "14", "15", "16", "MODP-1024", "MODP-2048", "MODP-3072", "MODP-4096"]:
        key_family = "Classical Modular Prime Exponentiation (MODP)"
        quantum_vulnerability = "CRITICAL (Shor's Algorithm breaks discrete logarithm problem in polynomial time)"
        pqc_checks.append({
            "control": "Key Exchange Quantum Resilience",
            "observed": f"Group {dh_group} ({key_family})",
            "status": "FAIL",
            "impact": "Vulnerable to Store-Now-Decrypt-Later (SNDL) attacks. Eavesdroppers recording encrypted traffic today will decrypt it when Quantum Computers arrive."
        })
    elif dh_group in ["19", "20", "21", "28", "31", "ECP-256", "ECP-384", "CURVE448"]:
        key_family = "Classical Elliptic Curve Cryptography (ECC / ECP)"
        quantum_vulnerability = "HIGH (Shor's Algorithm breaks elliptic curve discrete logarithms faster than RSA/MODP)"
        pqc_checks.append({
            "control": "Key Exchange Quantum Resilience",
            "observed": f"Group {dh_group} ({key_family})",
            "status": "WARNING",
            "impact": "High classical performance, but fully vulnerable to Quantum Shor's algorithm. Requires migration path to hybrid Post-Quantum ML-KEM (Kyber)."
        })
    elif "KYBER" in dh_group or "ML-KEM" in dh_group or "PQC" in dh_group:
        key_family = "Post-Quantum Hybrid Lattice-Based Cryptography (ML-KEM)"
        quantum_vulnerability = "NONE (Quantum Resistant - Lattice Math)"
        pqc_checks.append({
            "control": "Key Exchange Quantum Resilience",
            "observed": f"Group {dh_group} ({key_family})",
            "status": "PASS",
            "impact": "Quantum-Resistant. Protected against both classical supercomputers and future quantum computers."
        })
    else:
        key_family = f"Group {dh_group}"
        quantum_vulnerability = "UNKNOWN / Classical Baseline"
        pqc_checks.append({
            "control": "Key Exchange Quantum Resilience",
            "observed": f"Group {dh_group}",
            "status": "WARNING",
            "impact": "Unclassified key exchange group. Standard classical asymmetric algorithms are vulnerable to Quantum Shor's algorithm."
        })

    # 2. Symmetric Encryption Quantum Resilience (Grover's Algorithm)
    if "256" in enc_cipher or "CHACHA" in enc_cipher or "256-GCM" in enc_cipher:
        pqc_checks.append({
            "control": "Symmetric Cipher Quantum Strength (Grover's Algorithm)",
            "observed": f"{enc_cipher} (256-bit key)",
            "status": "PASS",
            "impact": "Grover's Quantum Search Algorithm reduces 256-bit keys to 128-bit quantum security, which remains mathematically unbreakable."
        })
        sym_quantum_status = "QUANTUM_RESISTANT"
    else:
        pqc_checks.append({
            "control": "Symmetric Cipher Quantum Strength (Grover's Algorithm)",
            "observed": f"{enc_cipher} (128-bit key)",
            "status": "WARNING",
            "impact": "Grover's Quantum Search Algorithm reduces 128-bit keys to 64-bit effective quantum security. Upgrade to 256-bit keys recommended."
        })
        sym_quantum_status = "QUANTUM_MARGINAL"

    # 3. Protocol Agility & RFC 8784 Hybrid Post-Quantum Rekeying Support
    if "V2" in ike_version or ike_version == "IKEV2":
        pqc_checks.append({
            "control": "Protocol Crypto-Agility (RFC 8784 / Hybrid PQ Support)",
            "observed": "IKEv2 (Supports Multiple Transform Substructures)",
            "status": "PASS",
            "impact": "IKEv2 supports RFC 8784 Post-Quantum Preshared Keys and hybrid key exchange extensions without requiring architecture redesign."
        })
        protocol_agility = "EXCELLENT"
    else:
        pqc_checks.append({
            "control": "Protocol Crypto-Agility (RFC 8784 / Hybrid PQ Support)",
            "observed": "IKEv1 (Fixed Transform Schema)",
            "status": "FAIL",
            "impact": "IKEv1 lacks modular transform negotiation capability required for Post-Quantum hybrid algorithms."
        })
        protocol_agility = "POOR"

    # Determine Overall PQC Status
    if any(c["status"] == "FAIL" for c in pqc_checks):
        pqc_status = "CLASSICAL_VULNERABLE"
        quantum_threat_rating = "HIGH_RISK_SNDL"
        readiness_score = 35
    elif any(c["status"] == "WARNING" for c in pqc_checks):
        pqc_status = "PQC_TRANSITIONAL"
        quantum_threat_rating = "MEDIUM_RISK"
        readiness_score = 70
    else:
        pqc_status = "PQC_READY"
        quantum_threat_rating = "QUANTUM_RESISTANT"
        readiness_score = 100

    return {
        "pqc_status": pqc_status,
        "quantum_threat_rating": quantum_threat_rating,
        "readiness_score": readiness_score,
        "key_exchange_family": key_family,
        "symmetric_quantum_status": sym_quantum_status,
        "crypto_agility_rating": protocol_agility,
        "pqc_checks": pqc_checks
    }
