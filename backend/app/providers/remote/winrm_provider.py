"""
Mission Control WinRM Provider

Mocked WinRM provider for Sprint 2.1.0.
Simulates WinRM connections without requiring pywinrm.

Sprint 2.1.0 - Remote Operations Framework.
"""

import asyncio
import logging
import random

from app.providers.remote.base_provider import RemoteBaseProvider

logger = logging.getLogger(__name__)


class WinRMProvider(RemoteBaseProvider):
    """
    Mocked WinRM provider.

    Simulates connection testing and command execution.
    Real WinRM via pywinrm added in Sprint 2.2.
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
        """Simulate WinRM connection test."""
        logger.info("WinRM: Testing connection to %s:%d", hostname, port)

        latency_ms = random.randint(80, 500)
        await asyncio.sleep(latency_ms / 1000)

        target = ip_address if ip_address else hostname

        return {
            "success": True,
            "latency_ms": latency_ms,
            "message": f"WinRM connection to {target}:{port} successful ({latency_ms}ms)",
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
        """Simulate WinRM command execution."""
        logger.info("WinRM: Executing '%s' on %s", command, hostname)

        latency_ms = random.randint(200, 1500)
        await asyncio.sleep(latency_ms / 1000)

        mock_outputs = {
            "hostname": hostname,
            "Get-Date": "Saturday, July 12, 2026 2:23:45 PM",
            "Get-Process | Measure-Object | Select-Object -ExpandProperty Count": "187",
            "Get-CimInstance Win32_OperatingSystem | Select-Object Caption": "\nCaption\n-------\nMicrosoft Windows Server 2022 Standard",
            "Get-Service | Where-Object {$_.Status -eq 'Running'} | Measure-Object | Select-Object -ExpandProperty Count": "94",
            "whoami": username,
            "Get-PSDrive | Select-Object Name,Used,Free": (
                "\nName   Used   Free\n----   ----   ----\nC    120GB  380GB\nD      0B    500GB"
            ),
        }

        stdout = mock_outputs.get(command, f"[mock output for: {command}]")

        return {
            "stdout": stdout,
            "stderr": "",
            "exit_code": 0,
            "duration_ms": latency_ms,
        }
