"""Mission Control Agent - Docker plugin for Windows."""

import asyncio
import json
import logging
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class DockerWindowsPlugin(AgentPlugin):
    """Docker Desktop inventory collector for Windows."""

    name = "docker"
    version = "3.0.0-rc1"
    description = "Docker Desktop inventory collector for Windows"
    platform_required = "windows"

    def __init__(self):
        self._context: dict[str, Any] = {}

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        try:
            ok = await self._check_docker()
            if ok:
                logger.info("Docker Desktop detected on Windows")
                return True
            logger.warning("Docker Desktop not available on this Windows host")
            return False
        except Exception as exc:
            logger.warning("Docker Windows init failed: %s", exc)
            return False

    async def _check_docker(self) -> bool:
        res = await self._powershell("docker --version")
        return bool(res and res.startswith("Docker version"))

    async def collect_inventory(self) -> dict[str, Any]:
        try:
            containers_json = await self._powershell(
                "docker ps -a --format '{{json .}}'"
            )
            images_json = await self._powershell("docker images --format '{{json .}}'")
            info_json = await self._powershell("docker info --format '{{json .}}'")

            containers = []
            for line in (containers_json or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.debug("Skipping unparsable docker ps line: %s", line)

            images = []
            for line in (images_json or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    images.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.debug("Skipping unparsable docker images line: %s", line)

            info = {}
            if info_json:
                try:
                    info = json.loads(info_json)
                except json.JSONDecodeError:
                    logger.debug("Failed to parse docker info JSON")

            return {
                "available": True,
                "version": info.get("ServerVersion")
                or info.get("Version")
                or "unknown",
                "container_count": len(containers),
                "image_count": len(images),
                "containers": [
                    {
                        "id": c.get("ID", ""),
                        "name": c.get("Names", ""),
                        "status": c.get("Status", ""),
                        "image": c.get("Image", ""),
                        "ports": [c.get("Ports", "")] if c.get("Ports") else [],
                    }
                    for c in containers[:100]
                ],
                "images": [
                    {
                        "id": i.get("ID", ""),
                        "tags": [i.get("Repository", ""), i.get("Tag", "")],
                        "size": i.get("Size", 0),
                    }
                    for i in images[:50]
                ],
            }
        except Exception as exc:
            logger.warning("Docker Windows inventory failed: %s", exc)
            return {"available": False, "error": str(exc)}

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        return {"success": False, "error": f"Unknown command: {command}"}

    async def _powershell(self, script: str) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            return stdout.decode("utf-8", errors="replace").strip()
        except Exception as exc:
            logger.debug("PowerShell command failed: %s", exc)
            return ""
