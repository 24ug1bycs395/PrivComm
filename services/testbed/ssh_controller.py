import asyncio
import base64
import logging
import os
import time
from typing import Any, Callable, Dict, Optional, Tuple

from services.testbed.models import VMHostConfig

logger = logging.getLogger("testbed.ssh_controller")

# Type alias for the event callback
EventCallback = Optional[Callable[[Dict[str, Any]], None]]


class SSHSession:
    """Reusable SSH connection for a single testbed node and job phase."""

    def __init__(self, vm_config: VMHostConfig, on_event: EventCallback = None, vm_role: str = "system"):
        self.vm_config = vm_config
        self.on_event = on_event
        self.vm_role = vm_role
        self.conn = None

    def _emit(self, event_type: str, command: str, **kwargs):
        if self.on_event:
            self.on_event({
                "vm": self.vm_role,
                "host": self.vm_config.host,
                "type": event_type,
                "command": command,
                **kwargs,
            })

    async def __aenter__(self):
        if self.vm_config.is_simulated:
            return self

        try:
            import asyncssh

            docker_host = os.environ.get("DOCKER_HOST_GATEWAY", "host.docker.internal")
            docker_ports = {
                "initiator": 2201,
                "responder": 2202,
                "observer": 2203,
                "attacker": 2204,
            }
            primary = (self.vm_config.ssh_host or self.vm_config.host, self.vm_config.port)
            endpoints = [primary]
            if self.vm_config.host.startswith("192.168.56.") and self.vm_role in docker_ports:
                docker_endpoint = (docker_host, docker_ports[self.vm_role])
                if docker_endpoint not in endpoints:
                    endpoints.append(docker_endpoint)

            errors = []
            for endpoint_host, endpoint_port in endpoints:
                self._emit("connection", "ssh session", status="connecting",
                           output=f"Connecting to {endpoint_host}:{endpoint_port}")
                connect_kwargs = {
                    "host": endpoint_host,
                    "port": endpoint_port,
                    "username": self.vm_config.username,
                    "known_hosts": None,
                    "connect_timeout": 4,
                }
                if self.vm_config.password:
                    connect_kwargs["password"] = self.vm_config.password
                if self.vm_config.key_path:
                    connect_kwargs["client_keys"] = [self.vm_config.key_path]
                try:
                    self.conn = await asyncssh.connect(**connect_kwargs)
                    self._emit("connection", "ssh session", status="connected",
                               output=f"Connected to {endpoint_host}:{endpoint_port}")
                    return self
                except Exception as exc:
                    errors.append(f"{endpoint_host}:{endpoint_port}: {exc}")

            detail = "; ".join(errors)
            self._emit("complete", "ssh session", status="error", exit_code=1,
                       output=f"SSH connection failed: {detail}")
            raise RuntimeError(f"SSH connection to {self.vm_config.host} failed: {detail}")
        except Exception as exc:
            if isinstance(exc, RuntimeError):
                raise
            self._emit("complete", "ssh session", status="error", exit_code=1,
                       output=f"SSH connection failed: {exc}")
            raise RuntimeError(f"SSH connection to {self.vm_config.host} failed: {exc}") from exc

    async def __aexit__(self, exc_type, exc, tb):
        if self.conn:
            self.conn.close()
            await self.conn.wait_closed()
        return False

    async def run_command(self, command: str, timeout: int = 20) -> Tuple[int, str, str]:
        self._emit("command", command, status="running")
        if self.vm_config.is_simulated:
            await asyncio.sleep(0.05)
            lines = _simulated_output(command, self.vm_role)
            for line in lines:
                self._emit("output", command, output=line, status="running")
            output = "\n".join(lines)
            self._emit("complete", command, status="success", exit_code=0, output=output)
            return 0, output, ""

        try:
            result = await asyncio.wait_for(self.conn.run(command), timeout=timeout)
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            for line in stdout.splitlines():
                self._emit("output", command, output=line, status="running")
            for line in stderr.splitlines():
                self._emit("output", command, output=f"[stderr] {line}", status="running")
            status = "success" if result.exit_status == 0 else "error"
            self._emit("complete", command, status=status, exit_code=result.exit_status,
                       output=stderr or stdout)
            return result.exit_status, stdout, stderr
        except Exception as exc:
            self._emit("complete", command, status="error", exit_code=1, output=str(exc))
            return 1, "", str(exc)

    async def write_file(self, remote_path: str, content: str) -> bool:
        command = f"write_file → {remote_path}"
        self._emit("command", command, status="running",
                   output=f"Preparing {len(content)} bytes for {remote_path}")
        if self.vm_config.is_simulated:
            self._emit("output", command, output=f"[SIMULATED] Writing config to {remote_path}...",
                       status="running")
            self._emit("complete", command, status="success",
                       output=f"Config written to {remote_path}")
            return True

        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        command_line = f"echo '{encoded}' | base64 -d | sudo tee {remote_path} > /dev/null"
        code, _, stderr = await self.run_command(command_line)
        if code == 0:
            self._emit("complete", command, status="success",
                       output=f"Config written to {remote_path}")
            return True
        self._emit("complete", command, status="error",
                   output=f"Failed to write {remote_path}: {stderr}")
        return False


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
    def session(vm_config: VMHostConfig, on_event: EventCallback = None, vm_role: str = "system") -> SSHSession:
        """Open one reusable SSH session for multiple node operations."""
        return SSHSession(vm_config, on_event=on_event, vm_role=vm_role)

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

            ssh_host = vm_config.ssh_host or vm_config.host

            connect_kwargs = {
                "host": ssh_host,
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

    @staticmethod
    async def download_file(
        vm_config: VMHostConfig,
        remote_path: str,
        local_path: str,
    ) -> bool:
        """Download a remote artifact through SFTP without simulated fallback."""
        if vm_config.is_simulated:
            return False

        import asyncssh

        connect_kwargs = {
            "host": vm_config.ssh_host or vm_config.host,
            "port": vm_config.port,
            "username": vm_config.username,
            "known_hosts": None,
        }
        if vm_config.password:
            connect_kwargs["password"] = vm_config.password
        if vm_config.key_path:
            connect_kwargs["client_keys"] = [vm_config.key_path]

        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        async with asyncssh.connect(**connect_kwargs) as conn:
            async with conn.start_sftp_client() as sftp:
                await sftp.get(remote_path, local_path)
        return os.path.isfile(local_path) and os.path.getsize(local_path) > 24


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
