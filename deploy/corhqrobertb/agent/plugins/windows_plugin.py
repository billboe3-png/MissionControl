"""Mission Control Agent - Windows platform plugin."""

import asyncio
import logging
import platform
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class WindowsPlugin(AgentPlugin):
    """Windows-specific inventory and management plugin."""

    name = "windows"
    version = "1.0.0"
    description = "Windows system management plugin"
    platform_required = "windows"

    def __init__(self):
        self._context: dict[str, Any] = {}

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        logger.info(
            "Windows plugin initialized for %s", platform.node()
        )
        return True

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect Windows-specific inventory."""
        return {
            "os_build": platform.version(),
            "computer_name": platform.node(),
            "hotfixes": await self._get_hotfixes(),
            "scheduled_tasks": await self._get_scheduled_tasks(),
            "windows_services": await self._get_services(),
        }

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Windows-specific commands."""
        handlers = {
            "get-service": self._get_service_status,
            "restart-service": self._restart_service,
            "event-log": self._get_event_log,
        }
        handler = handlers.get(command)
        if handler:
            return await handler(args)
        return {"success": False, "error": f"Unknown command: {command}"}

    async def _get_hotfixes(self) -> list[str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                "Get-HotFix | Select-Object -ExpandProperty HotFixID",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
            return [
                h.strip()
                for h in stdout.decode().strip().split("\n")
                if h.strip()
            ][:50]
        except Exception:
            return []

    async def _get_scheduled_tasks(self) -> list[dict[str, str]]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                "Get-ScheduledTask"
                " | Where-Object {$_.State -ne 'Disabled'}"
                " | Select-Object TaskName, TaskPath, State"
                " | ConvertTo-Json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
            import json

            data = json.loads(stdout.decode() or "[]")
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": t.get("TaskName", ""),
                    "path": t.get("TaskPath", ""),
                    "state": t.get("State", ""),
                }
                for t in data
            ][:50]
        except Exception:
            return []

    async def _get_services(self) -> list[dict[str, str]]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                "Get-Service"
                " | Where-Object {$_.Status -eq 'Running'}"
                " | Select-Object Name, DisplayName"
                " | ConvertTo-Json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
            import json

            data = json.loads(stdout.decode() or "[]")
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": s.get("Name", ""),
                    "display_name": s.get("DisplayName", ""),
                }
                for s in data
            ][:100]
        except Exception:
            return []

    async def _get_service_status(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        service = args.get("service", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell",
            "-Command",
            f"Get-Service '{service}'"
            " | Select-Object Name, Status, StartType"
            " | ConvertTo-Json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=30
        )
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
        }

    async def _restart_service(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        service = args.get("service", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell",
            "-Command",
            f"Restart-Service '{service}' -Force",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=60
        )
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
        }

    async def _get_event_log(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        log_name = args.get("log_name", "System")
        entries = args.get("entries", "50")
        proc = await asyncio.create_subprocess_exec(
            "powershell",
            "-Command",
            f"Get-EventLog -LogName '{log_name}'"
            f" -Newest {entries}"
            " | Select-Object TimeGenerated, EntryType,"
            " Source, Message | ConvertTo-Json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=30
        )
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
        }
