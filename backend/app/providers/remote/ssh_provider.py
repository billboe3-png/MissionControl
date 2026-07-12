"""
Mission Control SSH Provider

Mocked SSH provider for Sprint 2.1.0.
Simulates SSH connections without requiring paramiko.

Sprint 2.1.0 - Remote Operations Framework.
"""

import asyncio
import logging
import random

from app.providers.remote.base_provider import RemoteBaseProvider

logger = logging.getLogger(__name__)


class SSHProvider(RemoteBaseProvider):
    """
    Mocked SSH provider.

    Simulates connection testing and command execution.
    Real SSH via paramiko added in Sprint 2.2.
    """

    async def test_connection(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        ip_address: str | None,
    ) -> dict:
        """Simulate SSH connection test."""
        logger.info("SSH: Testing connection to %s:%d", hostname, port)

        latency_ms = random.randint(50, 300)
        await asyncio.sleep(latency_ms / 1000)

        target = ip_address if ip_address else hostname

        return {
            "success": True,
            "latency_ms": latency_ms,
            "message": f"SSH connection to {target}:{port} successful ({latency_ms}ms)",
        }

    async def execute_command(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        command: str,
        shell: str,
        ip_address: str | None,
    ) -> dict:
        """Simulate SSH command execution."""
        logger.info("SSH: Executing '%s' on %s", command, hostname)

        latency_ms = random.randint(100, 1000)
        await asyncio.sleep(latency_ms / 1000)

        target = ip_address if ip_address else hostname

        mock_outputs = {
            "hostname": f"{hostname}",
            "uptime": " 14:23:45 up 42 days, 3:17, 2 users, load average: 0.12, 0.08, 0.05",
            "df -h": (
                "Filesystem      Size  Used Avail Use% Mounted on\n"
                "/dev/sda1       50G   28G   20G  59% /\n"
                "tmpfs           32G     0   32G   0% /dev/shm"
            ),
            "free -h": (
                "              total        used        free      shared  buff/cache   available\n"
                "Mem:           64G        18G        22G        512M        24G        44G\n"
                "Swap:         8.0G        1.2G        6.8G"
            ),
            "whoami": username,
            "uname -a": f"Linux {hostname} 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux",
        }

        stdout = mock_outputs.get(command, f"[mock output for: {command}]")

        return {
            "stdout": stdout,
            "stderr": "",
            "exit_code": 0,
            "duration_ms": latency_ms,
        }
