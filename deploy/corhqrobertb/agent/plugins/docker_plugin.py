"""Mission Control Agent - Docker platform plugin."""

import logging
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class DockerPlugin(AgentPlugin):
    """Docker management plugin."""

    name = "docker"
    version = "1.0.0"
    description = "Docker container management plugin"
    platform_required = None

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._client = None

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        try:
            import docker

            self._client = docker.from_env()
            self._client.ping()
            logger.info("Docker plugin connected")
            return True
        except Exception as e:
            logger.warning("Docker not available: %s", e)
            return False

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect Docker inventory."""
        if not self._client:
            return {"available": False}

        try:
            containers = self._client.containers.list(all=True)
            images = self._client.images.list()
            info = self._client.info()
            return {
                "available": True,
                "version": info.get("ServerVersion", "unknown"),
                "container_count": len(containers),
                "image_count": len(images),
                "containers": [
                    {
                        "id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": str(c.image.tags)
                        if c.image.tags
                        else c.image.id[:12],
                        "ports": [
                            str(p)
                            for p in c.ports.values()
                        ]
                        if c.ports
                        else [],
                    }
                    for c in containers[:100]
                ],
                "images": [
                    {
                        "id": i.short_id,
                        "tags": i.tags,
                        "size": i.attrs.get("Size", 0),
                    }
                    for i in images[:50]
                ],
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Docker-specific commands."""
        if not self._client:
            return {
                "success": False,
                "error": "Docker not available",
            }

        handlers = {
            "container_start": self._start_container,
            "container_stop": self._stop_container,
            "container_restart": self._restart_container,
            "container_logs": self._container_logs,
            "container_inspect": self._container_inspect,
        }
        handler = handlers.get(command)
        if handler:
            return await handler(args)
        return {"success": False, "error": f"Unknown command: {command}"}

    async def _start_container(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        name = args.get("container", "")
        try:
            container = self._client.containers.get(name)
            container.start()
            return {
                "success": True,
                "stdout": f"Container {name} started",
                "exit_code": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": str(e),
                "exit_code": 1,
            }

    async def _stop_container(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        name = args.get("container", "")
        try:
            container = self._client.containers.get(name)
            container.stop()
            return {
                "success": True,
                "stdout": f"Container {name} stopped",
                "exit_code": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": str(e),
                "exit_code": 1,
            }

    async def _restart_container(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        name = args.get("container", "")
        try:
            container = self._client.containers.get(name)
            container.restart()
            return {
                "success": True,
                "stdout": f"Container {name} restarted",
                "exit_code": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": str(e),
                "exit_code": 1,
            }

    async def _container_logs(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        name = args.get("container", "")
        tail = args.get("tail", "100")
        try:
            container = self._client.containers.get(name)
            logs = container.logs(tail=int(tail)).decode(
                errors="replace"
            )
            return {
                "success": True,
                "stdout": logs,
                "exit_code": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": str(e),
                "exit_code": 1,
            }

    async def _container_inspect(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        name = args.get("container", "")
        try:
            container = self._client.containers.get(name)
            info = container.attrs
            return {
                "success": True,
                "stdout": str(info),
                "exit_code": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": str(e),
                "exit_code": 1,
            }
