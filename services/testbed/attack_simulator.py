"""Safe, control-plane attack simulations for the isolated testbed.

These simulations model expected telemetry and detection evidence only. They
do not inject traffic, alter host networking, or require an extra image.
"""

from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from services.testbed.models import TestbedTopology


class AttackType(str, Enum):
    MITM = "mitm"
    REPLAY = "replay"
    WEAK_PROPOSAL = "weak_proposal"
    TUNNEL_DISRUPTION = "tunnel_disruption"


class AttackSimulationRequest(BaseModel):
    attack_type: AttackType
    target: str = Field(default="gateway-1 ↔ gateway-2", max_length=80)
    topology: Optional[TestbedTopology] = None


class AttackSimulation(BaseModel):
    id: str
    attack_type: AttackType
    target: str
    status: str
    started_at: str
    stopped_at: Optional[str] = None
    detection: str
    evidence: List[str]


ATTACK_OPTIONS = [
    {
        "id": AttackType.MITM,
        "name": "Man-in-the-middle",
        "description": "Models an untrusted relay appearing between the VPN gateways.",
        "signal": "Peer path and identity mismatch",
    },
    {
        "id": AttackType.REPLAY,
        "name": "IKE / ESP replay",
        "description": "Models stale exchange and packet sequence observations.",
        "signal": "Duplicate sequence and nonce detection",
    },
    {
        "id": AttackType.WEAK_PROPOSAL,
        "name": "Weak proposal downgrade",
        "description": "Models a negotiation offering deprecated crypto suites.",
        "signal": "Policy rejected legacy proposal",
    },
    {
        "id": AttackType.TUNNEL_DISRUPTION,
        "name": "Tunnel disruption",
        "description": "Models scoped latency and tunnel flap telemetry.",
        "signal": "Child SA health degradation",
    },
]


_EVIDENCE = {
    AttackType.MITM: [
        "Attack VM inserted as a simulated relay",
        "Gateway identity and path consistency check raised",
        "No packets were sent outside the isolated testbed",
    ],
    AttackType.REPLAY: [
        "Synthetic stale sequence event generated",
        "Replay window would reject the observed sequence",
        "No packet capture was modified",
    ],
    AttackType.WEAK_PROPOSAL: [
        "Synthetic IKE proposal offered with legacy parameters",
        "Security policy would reject the negotiation",
        "No strongSwan configuration was changed",
    ],
    AttackType.TUNNEL_DISRUPTION: [
        "Synthetic latency spike and Child SA flap generated",
        "Tunnel health monitor would mark the path degraded",
        "No host routes or interfaces were modified",
    ],
}

_sessions: Dict[str, AttackSimulation] = {}
_lock = Lock()
_MAX_STORED_SESSIONS = 32


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_attack_status() -> dict:
    with _lock:
        sessions = list(_sessions.values())[-8:]
    return {
        "attack_vm": {
            "id": "attack-vm",
            "name": "Attack VM",
            "role": "Isolated simulator",
            "status": "running" if any(s.status == "running" for s in sessions) else "ready",
            "address": "192.168.56.40",
        },
        "options": ATTACK_OPTIONS,
        "sessions": sessions[-8:],
    }


def start_attack(request: AttackSimulationRequest) -> AttackSimulation:
    option = next(item for item in ATTACK_OPTIONS if item["id"] == request.attack_type)
    session = AttackSimulation(
        id=f"sim-{uuid4().hex[:8]}",
        attack_type=request.attack_type,
        target=request.target,
        status="running",
        started_at=_now(),
        detection=option["signal"],
        evidence=_EVIDENCE[request.attack_type],
    )
    with _lock:
        if any(existing.status == "running" for existing in _sessions.values()):
            raise RuntimeError("An attack simulation is already running.")
        _sessions[session.id] = session
        if len(_sessions) > _MAX_STORED_SESSIONS:
            completed_ids = [
                simulation_id
                for simulation_id, existing in _sessions.items()
                if existing.status != "running"
            ]
            for simulation_id in completed_ids[: len(_sessions) - _MAX_STORED_SESSIONS]:
                del _sessions[simulation_id]
    return session


def stop_attack(session_id: str) -> AttackSimulation:
    with _lock:
        session = _sessions.get(session_id)
        if not session:
            raise KeyError(session_id)
        if session.status != "running":
            return session
        session.status = "stopped"
        session.stopped_at = _now()
        _sessions[session_id] = session
        return session
