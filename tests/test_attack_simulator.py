import pytest
from fastapi.testclient import TestClient

from main import app
import routers.testbed as testbed_router
from services.testbed import attack_simulator


@pytest.fixture(autouse=True)
def clear_simulations(monkeypatch):
    with attack_simulator._lock:
        attack_simulator._sessions.clear()
    async def all_nodes_online(_topology):
        return {
            "all_online": True,
            "online_count": 3,
            "total_nodes": 3,
            "nodes": {},
        }
    monkeypatch.setattr(testbed_router, "_check_testbed_nodes", all_nodes_online)
    yield
    with attack_simulator._lock:
        attack_simulator._sessions.clear()


def test_attack_simulation_lifecycle_and_single_active_session():
    client = TestClient(app)

    started = client.post(
        "/api/testbed/attack-simulations",
        json={"attack_type": "mitm", "target": "gateway-1 to gateway-2"},
    )
    assert started.status_code == 200
    session = started.json()
    assert session["status"] == "running"
    assert session["attack_type"] == "mitm"

    overlapping = client.post(
        "/api/testbed/attack-simulations",
        json={"attack_type": "replay"},
    )
    assert overlapping.status_code == 409

    stopped = client.post(
        f"/api/testbed/attack-simulations/{session['id']}/stop"
    )
    assert stopped.status_code == 200
    stopped_session = stopped.json()
    assert stopped_session["status"] == "stopped"
    assert stopped_session["stopped_at"]

    repeated_stop = client.post(
        f"/api/testbed/attack-simulations/{session['id']}/stop"
    )
    assert repeated_stop.status_code == 200
    assert repeated_stop.json()["stopped_at"] == stopped_session["stopped_at"]


def test_unknown_attack_simulation_stop_returns_not_found():
    client = TestClient(app)

    response = client.post(
        "/api/testbed/attack-simulations/sim-does-not-exist/stop"
    )

    assert response.status_code == 404


def test_attack_simulation_requires_all_nodes_online(monkeypatch):
    async def one_node_offline(_topology):
        return {
            "all_online": False,
            "online_count": 2,
            "total_nodes": 3,
            "nodes": {"observer": {"status": "OFFLINE"}},
        }
    monkeypatch.setattr(testbed_router, "_check_testbed_nodes", one_node_offline)

    response = TestClient(app).post(
        "/api/testbed/attack-simulations",
        json={"attack_type": "mitm"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["online_count"] == 2
    assert response.json()["detail"]["total_nodes"] == 3


def test_attack_simulation_supports_fallback_mode_when_offline(monkeypatch):
    async def one_node_offline(_topology):
        return {
            "all_online": False,
            "online_count": 0,
            "total_nodes": 3,
            "nodes": {"initiator": {"status": "OFFLINE"}},
        }
    monkeypatch.setattr(testbed_router, "_check_testbed_nodes", one_node_offline)

    response = TestClient(app).post(
        "/api/testbed/attack-simulations",
        json={"attack_type": "mitm", "fallback": True},
    )

    assert response.status_code == 200
    session = response.json()
    assert session["status"] == "running"
    assert session["mode"] == "simulated_fallback"
    assert any("Fallback" in ev for ev in session["evidence"])
