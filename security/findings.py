from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class SecurityFinding:
    finding_id: str
    category: str
    severity: str  # HIGH, MEDIUM, LOW, INFO
    title: str
    observed: str
    expected: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
