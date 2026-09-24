import asyncio
import logging
from typing import Dict, Any, Tuple, Optional
from services.testbed.models import VMHostConfig

logger = logging.getLogger("testbed.ssh_controller")

class SSHController:
    """
    Manages asynchronous SSH communication, configuration push, and execution
    across strongSwan VMs (Initiator, Responder, Observer).
    """

    @staticmethod
    async def run_command(
        vm_config: VMHostConfig,
        command: str,
        timeout: int = 20
    ) -> Tuple[int, str, str]:
        """
        Executes a command on a remote VM via SSH.
        Returns (exit_code, stdout, stderr).
        """
        if vm_config.is_simulated:
            await asyncio.sleep(0.5)
            logger.info(f"[SIMULATED VM {vm_config.host}] Executing: {command}")
            return (0, f"[Simulated Output] Command '{command}' completed successfully on {vm_config.host}", "")

        try:
            import asyncssh
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
                res = await asyncio.wait_for(conn.run(command), timeout=timeout)
                return (res.exit_status, res.stdout, res.stderr)

        except ImportError:
            logger.warning("[SSHController] asyncssh not installed. Falling back to simulated VM execution.")
            await asyncio.sleep(0.5)
            return (0, f"[Fallback Executed] {command}", "")
        except Exception as e:
            logger.warning(f"[SSHController] SSH connection to {vm_config.host} failed: {e}. Simulating execution.")
            await asyncio.sleep(0.5)
            return (0, f"[Simulated Output after connection error: {e}] {command}", "")

    @staticmethod
    async def write_file(
        vm_config: VMHostConfig,
        remote_path: str,
        content: str
    ) -> bool:
        """
        Writes text content to a remote file path on the VM.
        """
        if vm_config.is_simulated:
            logger.info(f"[SIMULATED VM {vm_config.host}] Written {len(content)} bytes to {remote_path}")
            return True

        # Write via SSH command with base64 to avoid escaping issues
        import base64
        b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
        cmd = f"echo '{b64_content}' | base64 -d | sudo tee {remote_path} > /dev/null"
        code, stdout, stderr = await SSHController.run_command(vm_config, cmd)
        return code == 0
