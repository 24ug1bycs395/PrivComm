from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class SecurityFinding:
    finding_id: str
    category: str
    severity: str  # HIGH, MEDIUM, LOW, INFO
    title: str
    observed: str
    expected: str
    recommendation: str
    status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
