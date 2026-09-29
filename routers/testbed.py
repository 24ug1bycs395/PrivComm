import os
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse, JSONResponse
from services.testbed import event_store

from services.testbed.models import (
    ScenarioDefinition,
    TestbedRunRequest,
    TestbedJobStatus,
    TestbedTopology,
    TestbedState,
    PRESET_SCENARIOS
)
from services.testbed.orchestrator import TestbedOrchestrator
from db.repository import TestbedJobRepository
from services.testbed.attack_simulator import (
    AttackSimulationRequest,
    list_attack_status,
    start_attack,
    stop_attack,
)

router = APIRouter(prefix="/api/testbed", tags=["strongSwan IPsec Testbed"])
orchestrator = TestbedOrchestrator()


@router.get("/attack-simulations", summary="List safe attack simulation options and sessions")
async def get_attack_simulations():
    """Return control-plane simulations for the isolated Attack VM."""
    return list_attack_status()


@router.post("/attack-simulations", summary="Start a safe isolated attack simulation")
async def create_attack_simulation(request: AttackSimulationRequest, fallback: Optional[bool] = Query(None)):
    """Start a telemetry-only simulation; supports live testbed and offline fallback mode."""
    allow_fallback = fallback if fallback is not None else (request.fallback or request.mode == "simulated")
    node_status = await _check_testbed_nodes(request.topology or TestbedTopology())
    is_live = node_status["all_online"]

    if not is_live and not allow_fallback:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "All three testbed nodes must be online before starting an attack simulation, or enable fallback mode.",
                "online_count": node_status["online_count"],
                "total_nodes": node_status["total_nodes"],
                "nodes": node_status["nodes"],
            },
        )
    try:
        return start_attack(request, is_fallback=(not is_live))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/attack-simulations/{session_id}/stop", summary="Stop an attack simulation")
async def end_attack_simulation(session_id: str):
    try:
        return stop_attack(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Attack simulation '{session_id}' not found.")


@router.get("/scenarios", response_model=List[ScenarioDefinition], summary="List available testbed scenarios")
async def list_scenarios():
    """GET /api/testbed/scenarios: Returns built-in and custom scenario presets."""
    return PRESET_SCENARIOS


@router.post("/run", summary="Launch automated strongSwan testbed scenario execution")
async def run_testbed_scenario(request: TestbedRunRequest, background_tasks: BackgroundTasks):
    """
    POST /api/testbed/run
    Initiates asynchronous strongSwan provisioning, packet sniffing, traffic injection, and unified protocol analysis.
    """
    # 1. Resolve Scenario
    scenario: Optional[ScenarioDefinition] = None
    if request.custom_scenario:
        scenario = request.custom_scenario
    elif request.scenario_id:
        scenario = orchestrator.get_scenario_by_id(request.scenario_id)

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scenario '{request.scenario_id}' not found."
        )

    topology = request.topology or TestbedTopology()

    # 2. Create Job in Repository
    job = TestbedJobRepository.create_job(scenario.name, {
        "scenario": scenario.model_dump() if hasattr(scenario, "model_dump") else scenario.dict(),
        "topology": topology.model_dump() if hasattr(topology, "model_dump") else topology.dict()
    })

    # 3. Schedule Background Execution
    background_tasks.add_task(
        orchestrator.execute_scenario,
        job["id"],
        scenario,
        topology
    )

    return {
        "message": "Testbed scenario execution initiated successfully",
        "job_id": job["id"],
        "scenario_name": scenario.name,
        "state": "QUEUED"
    }


@router.get("/jobs", summary="List testbed execution jobs")
async def list_testbed_jobs(limit: int = Query(50, ge=1, le=100)):
    """GET /api/testbed/jobs: Returns history of strongSwan testbed runs."""
    return TestbedJobRepository.list_jobs(limit=limit)


@router.get("/jobs/{job_id}", summary="Get testbed execution job status and logs")
async def get_testbed_job_status(
    job_id: str,
    since_id: Optional[int] = Query(
        None,
        description="Only return terminal events with id > since_id (avoids duplicate events on each poll)."
    )
):
    """GET /api/testbed/jobs/{job_id}: Poll current state, live log output, and completed results.
    
    Merges transient in-memory terminal_events (keyed by VM role) into the response.
    Use ?since_id=<last_event_id> to fetch only new events and avoid re-sending the full list.
    """
    job = TestbedJobRepository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Testbed job '{job_id}' not found.")

    # Merge live terminal events from the in-memory ring-buffer
    terminal_events = event_store.get_events(job_id, since_id=since_id)
    job["terminal_events"] = terminal_events

    return job


@router.get("/jobs/{job_id}/pcap", summary="Download PCAP generated by testbed job")
async def download_testbed_pcap(job_id: str):
    """GET /api/testbed/jobs/{job_id}/pcap: Downloads captured PCAP file for the job."""
    job = TestbedJobRepository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pcap_path = job.get("pcap_storage_path")
    if not pcap_path or not os.path.exists(pcap_path):
        # Fallback to standard capture file if named
        files = [f for f in os.listdir("captures") if job_id[:8] in f] if os.path.exists("captures") else []
        if files:
            pcap_path = os.path.join("captures", files[0])
        else:
            sample_path = os.path.join("samples", "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
            if os.path.exists(sample_path):
                pcap_path = sample_path

    if not pcap_path or not os.path.exists(pcap_path):
        raise HTTPException(status_code=404, detail="PCAP file for this testbed job not found.")

    return FileResponse(
        pcap_path,
        media_type="application/vnd.tcpdump.pcap",
        filename=os.path.basename(pcap_path)
    )


async def _probe_node(role: str, host: str, port: int = 22, username: str = "vagrant", password: str = "vagrant", timeout: float = 2.0) -> dict:
    import time
    
    # host.docker.internal resolves to the Windows host from inside Docker containers
    # This allows the backend container to reach testbed containers via mapped host ports
    docker_host = os.environ.get("DOCKER_HOST_GATEWAY", "host.docker.internal")
    port_fallbacks = {
        "initiator": (docker_host, 2201),
        "responder": (docker_host, 2202),
        "observer": (docker_host, 2203),
        "attacker": (docker_host, 2204),
    }

    endpoints_to_try = [(host, port)]
    if host.startswith("192.168.56.") and role in port_fallbacks:
        fb_host, fb_port = port_fallbacks[role]
        if (fb_host, fb_port) not in endpoints_to_try:
            endpoints_to_try.append((fb_host, fb_port))

    last_error = None
    for cur_host, cur_port in endpoints_to_try:
        try:
            t_start = time.monotonic()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(cur_host, cur_port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            latency_ms = round((time.monotonic() - t_start) * 1000, 1)

            # Fast SSH banner/command check
            details = f"SSH reachable on {cur_host}:{cur_port}"
            try:
                import asyncssh
                async with asyncssh.connect(
                    host=cur_host, port=cur_port, username=username, password=password,
                    known_hosts=None, login_timeout=2.0
                ) as conn:
                    res = await asyncio.wait_for(conn.run("uname -s -r 2>/dev/null || hostname", timeout=2.0), timeout=2.0)
                    if res.stdout:
                        details = res.stdout.strip()
            except Exception:
                pass

            return {
                "role": role,
                "host": host if cur_host in ("127.0.0.1", docker_host) else cur_host,
                "port": cur_port,
                "status": "ONLINE",
                "latency_ms": latency_ms,
                "details": details,
                "error": None
            }
        except Exception as exc:
            last_error = str(exc)
            continue

    return {
        "role": role,
        "host": host,
        "port": port,
        "status": "OFFLINE",
        "latency_ms": None,
        "details": "Unreachable / Port closed",
        "error": last_error
    }


@router.get("/check-nodes", summary="Test SSH & connectivity of the 3 testbed containers/VMs")
@router.post("/check-nodes", summary="Test SSH & connectivity of the 3 testbed containers/VMs")
async def check_testbed_nodes(topology: Optional[TestbedTopology] = None):
    """
    Probes all 3 testbed nodes (Initiator, Responder, Observer) in parallel
    and returns their live online/offline status, latency, and system info.
    """
    return await _check_testbed_nodes(topology or TestbedTopology())


async def _check_testbed_nodes(top: TestbedTopology) -> dict:
    results = await asyncio.gather(
        _probe_node("initiator", top.initiator.host, top.initiator.port, top.initiator.username, top.initiator.password or "vagrant"),
        _probe_node("responder", top.responder.host, top.responder.port, top.responder.username, top.responder.password or "vagrant"),
        _probe_node("observer", top.observer.host, top.observer.port, top.observer.username, top.observer.password or "vagrant")
    )

    all_online = all(r["status"] == "ONLINE" for r in results)
    online_count = sum(1 for r in results if r["status"] == "ONLINE")

    return {
        "all_online": all_online,
        "online_count": online_count,
        "total_nodes": 3,
        "nodes": {
            "initiator": results[0],
            "responder": results[1],
            "observer": results[2]
        }
    }
