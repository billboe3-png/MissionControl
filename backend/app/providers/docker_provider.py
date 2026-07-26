"""
Mission Control Docker Provider

Returns live Docker container information using the existing Docker SDK.
Expands the basic container list with detailed metrics.
Gracefully handles Docker unavailable.
"""

import logging

from app.infrastructure.docker import get_docker_provider

logger = logging.getLogger(__name__)


class DockerProvider:
    """Return live Docker engine and container data."""

    async def get_docker_data(self) -> dict:
        """Return full Docker status including per-container details."""
        try:
            docker = get_docker_provider()

            version_data = await docker.version()
            await docker.info()
            containers_raw = await docker.containers()

            if not version_data:
                return self._unavailable("Docker engine not responding")

            engine_running = True
            docker_version = version_data.get("Version", "Unknown")
            compose_version = "sdk"
            containers = []

            for c in containers_raw:
                state = c.get("state", "unknown")
                status = c.get("status", "unknown")

                container_detail = {
                    "id": c.get("id", ""),
                    "name": c.get("name", ""),
                    "image": c.get("image", "<none>"),
                    "status": status,
                    "state": state,
                    "cpu_percent": None,
                    "memory_percent": None,
                    "restart_count": None,
                    "ports": [],
                    "health": None,
                    "created": None,
                    "uptime": None,
                }

                try:
                    docker_client = docker.sdk.client
                    if docker_client:
                        full_container = docker_client.containers.get(c.get("name", ""))
                        inspect = full_container.attrs

                        state_config = inspect.get("State", {})
                        container_detail["restart_count"] = state_config.get(
                            "RestartCount", 0
                        )
                        container_detail["health"] = (
                            state_config.get("Health", {}).get("Status")
                        )
                        container_detail["created"] = inspect.get("Created")

                        started_at = state_config.get("StartedAt")
                        if started_at and started_at != "0001-01-01T00:00:00Z":
                            container_detail["uptime"] = started_at

                        port_bindings = inspect.get("NetworkSettings", {}).get(
                            "Ports", {}
                        )
                        ports = []
                        for container_port, bindings in port_bindings.items():
                            if bindings:
                                for binding in bindings:
                                    ports.append(
                                        f"{binding.get('HostIp', '0.0.0.0')}:{binding.get('HostPort', '')}->{container_port}"
                                    )
                            else:
                                ports.append(container_port)
                        container_detail["ports"] = ports

                except Exception:
                    pass

                containers.append(container_detail)

            running = len([c for c in containers if c["state"] == "running"])
            stopped = len([c for c in containers if c["state"] == "exited"])

            image_count = 0
            try:
                docker_client = docker.sdk.client
                if docker_client:
                    image_count = len(docker_client.images.list())
            except Exception:
                pass

            return {
                "available": True,
                "engine": "running" if engine_running else "offline",
                "docker_version": docker_version,
                "compose_version": compose_version,
                "container_count": len(containers),
                "running": running,
                "stopped": stopped,
                "image_count": image_count,
                "containers": containers,
            }

        except Exception as exc:
            logger.warning("Docker provider failed: %s", exc)
            return self._unavailable(str(exc))

    @staticmethod
    def _unavailable(reason: str) -> dict:
        return {
            "available": False,
            "engine": "offline",
            "docker_version": None,
            "compose_version": None,
            "container_count": 0,
            "running": 0,
            "stopped": 0,
            "image_count": 0,
            "containers": [],
            "reason": reason,
        }


docker_provider = DockerProvider()
