"""Mission Control Agent - Linux platform plugin."""

import asyncio
import logging
import os
import platform
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class LinuxPlugin(AgentPlugin):
    """Linux-specific inventory and management plugin."""

    name = "linux"
    version = "3.0.0-rc1"
    description = "Linux system management plugin"
    platform_required = "linux"

    def __init__(self):
        self._context: dict[str, Any] = {}

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        logger.info("Linux plugin initialized for %s", platform.node())
        return True

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect Linux-specific inventory."""
        data: dict[str, Any] = {
            "kernel": platform.release(),
            "distro": self._get_distro(),
            "systemd_services": await self._get_systemd_services(),
            "cron_jobs": self._get_cron_jobs(),
            "users": self._get_users(),
        }
        return data

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Linux-specific commands."""
        handlers = {
            "systemctl": self._systemctl,
            "journalctl": self._journalctl,
            "disk_usage": self._disk_usage,
        }
        handler = handlers.get(command)
        if handler:
            return await handler(args)
        return {"success": False, "error": f"Unknown command: {command}"}

    def _get_distro(self) -> str:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
        return platform.platform()

    async def _get_systemd_services(self) -> list[dict[str, str]]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-pager",
                "--no-legend",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            services = []
            for line in stdout.decode().strip().split("\n"):
                parts = line.split(None, 4)
                if len(parts) >= 4:
                    services.append(
                        {
                            "name": parts[0],
                            "load": parts[1],
                            "active": parts[2],
                            "sub": parts[3],
                        }
                    )
            return services[:50]
        except Exception:
            return []

    def _get_cron_jobs(self) -> list[str]:
        try:
            cron_dir = "/etc/cron.d"
            if os.path.isdir(cron_dir):
                return os.listdir(cron_dir)[:20]
        except Exception:
            pass
        return []

    def _get_users(self) -> list[str]:
        try:
            with open("/etc/passwd") as f:
                return [line.split(":")[0] for line in f if not line.startswith("#")][
                    :100
                ]
        except Exception:
            return []

    async def _systemctl(self, args: dict[str, Any]) -> dict[str, Any]:
        action = args.get("action", "status")
        service = args.get("service", "")
        proc = await asyncio.create_subprocess_exec(
            "systemctl",
            action,
            service,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
        }

    async def _journalctl(self, args: dict[str, Any]) -> dict[str, Any]:
        lines = args.get("lines", "50")
        service = args.get("service", "")
        cmd = ["journalctl", "-n", lines, "--no-pager"]
        if service:
            cmd.extend(["-u", service])
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
        }

    async def _disk_usage(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "/")
        proc = await asyncio.create_subprocess_exec(
            "df",
            "-h",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "exit_code": proc.returncode,
        }
