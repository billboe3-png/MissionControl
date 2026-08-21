"""
Mission Control Agent - MikroTik RouterOS plugin.

Cross-platform implementation using SSH:
- Collects interface, firewall, DHCP lease, and system resource data
- Can proxy WebFig-style access or execute arbitrary commands
"""

import asyncio
import logging
import os
from typing import Any

try:
    import asyncssh

    _HAS_ASYNCSSH = True
except ImportError:  # pragma: no cover - optional dependency
    _HAS_ASYNCSSH = False

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")

_MIKROTIK_HOST = os.environ.get("MC_MIKROTIK_HOST", "")
_MIKROTIK_PORT = int(os.environ.get("MC_MIKROTIK_PORT", "22"))
_MIKROTIK_USERNAME = os.environ.get("MC_MIKROTIK_USERNAME", "")
_MIKROTIK_PASSWORD = os.environ.get("MC_MIKROTIK_PASSWORD", "")


class MikroTikPlugin(AgentPlugin):
    """MikroTik RouterOS SSH access plugin."""

    name = "mikrotik"
    version = "1.0.0"
    description = "MikroTik RouterOS SSH/console access"
    platform_required = None  # cross-platform

    def __init__(self) -> None:
        self._context: dict[str, Any] = {}
        self._host = _MIKROTIK_HOST
        self._port = _MIKROTIK_PORT
        self._username = _MIKROTIK_USERNAME
        self._password = _MIKROTIK_PASSWORD

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._host = self._context.get("mikrotik", {}).get("host") or _MIKROTIK_HOST
        self._port = int(self._context.get("mikrotik", {}).get("port") or _MIKROTIK_PORT)
        self._username = self._context.get("mikrotik", {}).get("username") or _MIKROTIK_USERNAME
        self._password = self._context.get("mikrotik", {}).get("password") or _MIKROTIK_PASSWORD
        if not self._host or not self._username or not self._password:
            logger.warning("MikroTik plugin initialized without complete credentials")
        return True

    async def collect_inventory(self) -> dict[str, Any]:
        if not _HAS_ASYNCSSH:
            return {"available": False, "error": "asyncssh is not installed"}

        if not self._host or not self._username or not self._password:
            return {"available": False, "error": "Missing MikroTik credentials"}

        try:
            output = await self._execute("/system resource print")
            system = self._parse_resource(output)

            interfaces = []
            iface_output = await self._execute("/interface print detail")
            interfaces = self._parse_interfaces(iface_output)

            firewall = []
            fw_output = await self._execute("/ip firewall filter print detail")
            firewall = self._parse_firewall(fw_output)

            dhcp = []
            dhcp_output = await self._execute("/ip dhcp-server lease print detail")
            dhcp = self._parse_dhcp(dhcp_output)

            return {
                "available": True,
                "host": self._host,
                "port": self._port,
                "system": system,
                "interfaces": interfaces,
                "firewall": firewall,
                "dhcp": dhcp,
            }
        except Exception as exc:
            logger.warning("MikroTik inventory collection failed: %s", exc)
            return {"available": False, "error": str(exc)}

    async def test_connection(self) -> dict[str, Any]:
        if not _HAS_ASYNCSSH:
            return {"connected": False, "error": "asyncssh is not installed"}

        if not self._host or not self._username or not self._password:
            return {"connected": False, "error": "Missing MikroTik credentials"}

        try:
            output = await self._execute("/system resource print")
            version = ""
            board = ""
            for line in output.splitlines():
                if line.startswith("version="):
                    version = line.split("=", 1)[1].strip()
                elif line.startswith("board-name="):
                    board = line.split("=", 1)[1].strip()
            return {
                "connected": True,
                "version": version,
                "board": board,
                "host": self._host,
            }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        if command == "test_connection":
            result = await self.test_connection()
            return {
                "success": result.get("connected", False),
                "stdout": str(result),
                "stderr": str(result.get("error", "")),
                "exit_code": 0 if result.get("connected") else 1,
            }
        if command == "collect":
            data = await self.collect_inventory()
            return {
                "success": data.get("available", False),
                "stdout": str(data),
                "stderr": str(data.get("error", "")),
                "exit_code": 0 if data.get("available") else 1,
            }
        try:
            output = await self._execute(command)
            return {"success": True, "output": output, "stdout": output, "stderr": "", "exit_code": 0}
        except Exception as exc:
            return {"success": False, "output": "", "stdout": "", "stderr": str(exc), "exit_code": 1}

    async def _execute(self, command: str) -> str:
        if not _HAS_ASYNCSSH:
            raise RuntimeError("asyncssh is not installed")

        async with asyncssh.connect(
            self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            known_hosts=None,
            connect_timeout=20,
        ) as conn:
            result = await conn.run(command, check=True)
            return (result.stdout or "").strip()

    @staticmethod
    def _parse_resource(output: str) -> dict[str, str]:
        data: dict[str, str] = {}
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
        return data

    @staticmethod
    def _parse_interfaces(output: str) -> list[dict[str, str]]:
        interfaces: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in output.splitlines():
            if line.startswith("Flags:"):
                if current:
                    interfaces.append(current)
                current = {}
            if "=" in line:
                key, value = line.split("=", 1)
                current[key.strip()] = value.strip()
        if current:
            interfaces.append(current)
        return interfaces

    @staticmethod
    def _parse_firewall(output: str) -> list[dict[str, str]]:
        rules: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in output.splitlines():
            if line.startswith("Flags:"):
                if current:
                    rules.append(current)
                current = {}
            if "=" in line:
                key, value = line.split("=", 1)
                current[key.strip()] = value.strip()
        if current:
            rules.append(current)
        return rules

    @staticmethod
    def _parse_dhcp(output: str) -> list[dict[str, str]]:
        leases: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in output.splitlines():
            if line.startswith("Flags:"):
                if current:
                    leases.append(current)
                current = {}
            if "=" in line:
                key, value = line.split("=", 1)
                current[key.strip()] = value.strip()
        if current:
            leases.append(current)
        return leases
