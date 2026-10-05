from typing import Any, Dict, List

from security.findings import SecurityFinding


def generate_recommendations(findings: List[SecurityFinding]) -> List[Dict[str, Any]]:
    """
    Generate structured, actionable recommendations for each confirmed policy finding.
    Kept separate from protocol parsing logic.
    """
    recommendations = []

    for f in findings:
        rec = {
            "finding_id": f.finding_id,
            "category": f.category,
            "severity": f.severity,
            "current_configuration": f.observed,
            "expected_configuration": f.expected,
            "reason": f.title,
            "recommended_action": f.recommendation
        }
        recommendations.append(rec)

    return recommendations
