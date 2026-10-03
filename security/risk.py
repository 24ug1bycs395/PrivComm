from typing import Any, Dict, List

from security.findings import SecurityFinding
from security.policy_engine import load_security_policy


def calculate_security_risk(findings: List[SecurityFinding], policy_path: str = None) -> Dict[str, Any]:
    """
    Calculate deterministic security risk score and risk level based on confirmed findings.
    Methodology: Policy-weighted severity summation capped at 100.
    """
    policy = load_security_policy(policy_path) if policy_path else load_security_policy()
    weights = policy.get("risk_weights", {"HIGH": 30, "MEDIUM": 15, "LOW": 5})

    raw_score = 0
    for f in findings:
        if getattr(f, "status", None) == "not_observable":
            continue
        sev = f.severity.upper()
        raw_score += weights.get(sev, 10)

    score = min(100, raw_score)

    if score == 0:
        level = "SECURE"
    elif score <= 25:
        level = "LOW"
    elif score <= 55:
        level = "MEDIUM"
    elif score <= 85:
        level = "HIGH"
    else:
        level = "CRITICAL"

    return {
        "score": score,
        "level": level,
        "method": "deterministic_policy_weighting",
        "methodology_description": "Risk score is calculated deterministically by weighting confirmed findings (HIGH=30, MEDIUM=15, LOW=5) against configured policy baseline."
    }
