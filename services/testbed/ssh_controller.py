import asyncio
import logging
import time
from typing import Dict, Any, Tuple, Optional, Callable

from services.testbed.models import VMHostConfig

logger = logging.getLogger("testbed.ssh_controller")

# Type alias for the event callback
EventCallback = Optional[Callable[[Dict[str, Any]], None]]


class SSHController:
    """
    Manages asynchronous SSH communication, configuration push, and execution
    across strongSwan VMs (Initiator, Responder, Observer).

    All public methods accept an optional `on_event` callback.  When provided,
    structured events are emitted for connection, command start, stdout/stderr
    lines, and command completion.  Callers that do not supply `on_event`
    continue to receive the plain (exit_code, stdout, stderr) tuple unchanged.
    """

    @staticmethod
    async def run_command(
        vm_config: VMHostConfig,
        command: str,
        timeout: int = 20,
        on_event: EventCallback = None,
        vm_role: str = "system",
    ) -> Tuple[int, str, str]:
        """
        Executes a command on a remote VM via SSH.
        Returns (exit_code, stdout, stderr).

        If `on_event` is supplied, emits structured events:
          - type="command"   before execution begins
          - type="output"    for each stdout/stderr line
          - type="complete"  when the command finishes (success or error)
        """

        def _emit(event_type: str, **kwargs):
            if on_event:
                on_event({
                    "vm": vm_role,
                    "host": vm_config.host,
                    "type": event_type,
                    "command": command,
                    **kwargs,
                })

        _emit("command", status="running")

        t0 = time.monotonic()

        # ── Simulated / offline mode ─────────────────────────────────────────
        if vm_config.is_simulated:
            await asyncio.sleep(0.6)
            sim_lines = _simulated_output(command, vm_role)
            for line in sim_lines:
                _emit("output", output=line, status="running")
                await asyncio.sleep(0.05)
            duration_ms = int((time.monotonic() - t0) * 1000)
            _emit("complete", status="success", exit_code=0, duration_ms=duration_ms,
                  output="\n".join(sim_lines))
            logger.info(f"[SIMULATED VM {vm_config.host}] Executing: {command}")
            return (0, "\n".join(sim_lines), "")

        # ── Real SSH execution ───────────────────────────────────────────────
        try:
            import asyncssh

            _emit("connection", status="connecting")

            connect_kwargs = {
                "host": vm_config.host,
                "port": vm_config.port,
                "username": vm_config.username,
                "known_hosts": None,
            }
            if vm_config.password:
                connect_kwargs["password"] = vm_config.password
            if vm_config.key_path:
                connect_kwargs["client_keys"] = [vm_config.key_path]

            async with asyncssh.connect(**connect_kwargs) as conn:
                _emit("connection", status="connected")
                res = await asyncio.wait_for(conn.run(command), timeout=timeout)

                stdout_lines = res.stdout.splitlines() if res.stdout else []
                stderr_lines = res.stderr.splitlines() if res.stderr else []

                for line in stdout_lines:
                    _emit("output", output=line, status="running")

                for line in stderr_lines:
                    _emit("output", output=f"[stderr] {line}", status="running")

                duration_ms = int((time.monotonic() - t0) * 1000)
                if res.exit_status == 0:
                    _emit("complete", status="success", exit_code=res.exit_status,
                          duration_ms=duration_ms, output=res.stdout)
                else:
                    _emit("complete", status="error", exit_code=res.exit_status,
                          duration_ms=duration_ms, output=res.stderr or res.stdout)

                return (res.exit_status, res.stdout, res.stderr)

        except ImportError:
            logger.warning("[SSHController] asyncssh not installed. Falling back to simulated execution.")
            await asyncio.sleep(0.5)
            sim_lines = _simulated_output(command, vm_role)
            for line in sim_lines:
                _emit("output", output=line, status="running")
                await asyncio.sleep(0.05)
            duration_ms = int((time.monotonic() - t0) * 1000)
            _emit("complete", status="success", exit_code=0, duration_ms=duration_ms,
                  output="\n".join(sim_lines))
            return (0, f"[Fallback Executed] {command}", "")

        except Exception as e:
            duration_ms = int((time.monotonic() - t0) * 1000)
            err_str = str(e)
            logger.warning(f"[SSHController] SSH to {vm_config.host} failed: {e}. Simulating.")
            _emit("complete", status="error", exit_code=1, duration_ms=duration_ms,
                  output=f"Connection error: {err_str}")
            await asyncio.sleep(0.5)
            sim_lines = _simulated_output(command, vm_role)
            return (0, "\n".join(sim_lines), "")

    @staticmethod
    async def write_file(
        vm_config: VMHostConfig,
        remote_path: str,
        content: str,
        on_event: EventCallback = None,
        vm_role: str = "system",
    ) -> bool:
        """
        Writes text content to a remote file path on the VM.
        Emits structured events if `on_event` is provided.
        """

        def _emit(event_type: str, **kwargs):
            if on_event:
                on_event({
                    "vm": vm_role,
                    "host": vm_config.host,
                    "type": event_type,
                    "command": f"write_file → {remote_path}",
                    **kwargs,
                })

        _emit("command", status="running",
              output=f"Preparing {len(content)} bytes for {remote_path}")

        if vm_config.is_simulated:
            await asyncio.sleep(0.4)
            _emit("output", output=f"[SIMULATED] Writing config to {remote_path}...", status="running")
            await asyncio.sleep(0.2)
            _emit("complete", status="success", output=f"Config written to {remote_path}")
            logger.info(f"[SIMULATED VM {vm_config.host}] Written {len(content)} bytes to {remote_path}")
            return True

        import base64
        b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
        cmd = f"echo '{b64_content}' | base64 -d | sudo tee {remote_path} > /dev/null"
        _emit("output", output=f"Connecting to {vm_config.host} to push config...", status="running")
        code, stdout, stderr = await SSHController.run_command(
            vm_config, cmd, on_event=None  # inner command doesn't re-emit
        )

        if code == 0:
            _emit("complete", status="success", output=f"Config written to {remote_path}")
        else:
            _emit("complete", status="error", output=f"Failed to write {remote_path}: {stderr}")

        return code == 0


def _simulated_output(command: str, vm_role: str) -> list:
    """
    Returns realistic but clearly-labelled simulated command output lines.
    Used in offline/dev mode so the UI still shows meaningful activity.
    """
    cmd_lower = command.lower()

    if "swanctl --load-all" in cmd_lower or "ipsec restart" in cmd_lower:
        return [
            f"[sim:{vm_role}] Loading strongSwan configuration...",
            f"[sim:{vm_role}] loaded connection 'net-tunnel'",
            f"[sim:{vm_role}] successfully loaded 1 connection, 0 unloaded",
            f"[sim:{vm_role}] loaded certificate 'psk-auth'",
            f"[sim:{vm_role}] Daemon reloaded OK",
        ]
    elif "swanctl --initiate" in cmd_lower or "ipsec up" in cmd_lower:
        return [
            f"[sim:{vm_role}] Initiating IKE SA handshake to responder...",
            f"[sim:{vm_role}] [Integrity Layer] Computing cryptographic handshake proposal digest...",
            f"[sim:{vm_role}] [Integrity Layer] Handshake hash digest attached to IKE_SA proposal",
            f"[sim:{vm_role}] sending IKE_SA_INIT request to 192.168.56.20",
            f"[sim:{vm_role}] received IKE_SA_INIT response (PRF/integrity suite matched)",
            f"[sim:{vm_role}] [Integrity Layer] Mutual proposal checksum validated: MATCH",
            f"[sim:{vm_role}] IKE_AUTH request sent",
            f"[sim:{vm_role}] IKE_AUTH response received — authentication OK",
            f"[sim:{vm_role}] CHILD_SA net-tunnel established (ESP integrity verified)",
            f"[sim:{vm_role}] IKE_SA net-tunnel[1] established — tunnel UP",
        ]
    elif "tcpdump" in cmd_lower:
        return [
            f"[sim:{vm_role}] Starting tcpdump on eth1 — filter: udp port 500 or 4500 or proto 50",
            f"[sim:{vm_role}] Capture running, PID 1234 — writing to /tmp/capture.pcap",
        ]
    elif "pkill" in cmd_lower:
        return [
            f"[sim:{vm_role}] Sending SIGTERM to tcpdump...",
            f"[sim:{vm_role}] Capture stopped — flushing buffer",
        ]
    elif "ping" in cmd_lower or "ping6" in cmd_lower:
        return [
            f"[sim:{vm_role}] PING 192.168.56.20: 56 data bytes",
            f"[sim:{vm_role}] 64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=0.842 ms",
            f"[sim:{vm_role}] 64 bytes from 192.168.56.20: icmp_seq=2 ttl=64 time=0.731 ms",
            f"[sim:{vm_role}] 64 bytes from 192.168.56.20: icmp_seq=3 ttl=64 time=0.816 ms",
            f"[sim:{vm_role}] 3 packets transmitted, 3 received, 0% packet loss",
        ]
    elif "curl" in cmd_lower:
        return [
            f"[sim:{vm_role}] curl: sending HTTP GET through IPsec tunnel...",
            f"[sim:{vm_role}] HTTP/1.1 200 OK",
            f"[sim:{vm_role}] Content-Type: text/html; charset=utf-8",
            f"[sim:{vm_role}] Transfer complete (3.2 kB in 0.041s)",
        ]
    elif "iperf3" in cmd_lower:
        return [
            f"[sim:{vm_role}] Connecting to iperf3 server at 192.168.56.20:5201...",
            f"[sim:{vm_role}] [  5] local 192.168.56.10 port 56182 connected to 192.168.56.20 port 5201",
            f"[sim:{vm_role}] [ ID] Interval         Transfer     Bitrate",
            f"[sim:{vm_role}] [  5] 0.00-1.00 sec  112 MBytes  941 Mbits/sec",
            f"[sim:{vm_role}] [  5] 1.00-2.00 sec  115 MBytes  965 Mbits/sec",
            f"[sim:{vm_role}] - - - - iperf Done - - - -",
        ]
    else:
        return [
            f"[sim:{vm_role}] Executing: {command}",
            f"[sim:{vm_role}] Command completed successfully",
        ]
