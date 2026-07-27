"""
Docker Plugin API Client

Async HTTP client for Docker Engine API.
Handles local Unix socket and remote TCP connections.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any

import httpx

logger = logging.getLogger("plugin.docker.api")


class DockerApiClient:
    """Async Docker Engine API client."""

    def __init__(
        self,
        host: str = "",
        tls: bool = False,
        tls_cert_path: str = "",
        tls_verify: bool = True,
        timeout: int = 30,
        retries: int = 3,
    ) -> None:
        self._host = host.rstrip("/")
        self._tls = tls
        self._tls_cert_path = tls_cert_path
        self._tls_verify = tls_verify
        self._timeout = timeout
        self._retries = retries
        self._client: httpx.AsyncClient | None = None

    def _base_url(self) -> str:
        if self._host:
            scheme = "https" if self._tls else "http"
            return f"{scheme}://{self._host}"
        return "http://localhost"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self._tls_verify if self._tls else False,
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _get(self, path: str) -> Any:
        """Execute a GET request with retries."""
        client = await self._get_client()
        url = f"{self._base_url()}{path}"

        last_error: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, Exception) as exc:
                last_error = exc
                logger.debug("Attempt %d/%d failed: %s", attempt, self._retries, exc)
                if attempt < self._retries:
                    await asyncio.sleep(1)
        raise RuntimeError(
            f"Docker API call '{path}' failed after {self._retries} attempts: {last_error}"
        )

    async def test_connection(self) -> dict[str, Any]:
        try:
            data = await self._get("/_ping")
            return {"healthy": True, "data": data}
        except Exception as exc:
            return {"healthy": False, "error": str(exc)}

    async def get_info(self) -> dict[str, Any]:
        return await self._get("/info")

    async def get_version(self) -> dict[str, Any]:
        return await self._get("/version")

    async def get_containers(self, all: bool = True) -> list[dict[str, Any]]:
        path = "/containers/json"
        if all:
            path += "?all=true"
        data = await self._get(path)
        return data if isinstance(data, list) else data.get("data", [])

    async def get_container_stats(self, container_id: str) -> dict[str, Any]:
        path = f"/containers/{container_id}/stats?stream=false"
        return await self._get(path)

    async def get_container_inspect(self, container_id: str) -> dict[str, Any]:
        return await self._get(f"/containers/{container_id}/json")

    async def get_images(self) -> list[dict[str, Any]]:
        data = await self._get("/images/json")
        return data if isinstance(data, list) else data.get("data", [])

    async def get_volumes(self) -> list[dict[str, Any]]:
        data = await self._get("/volumes")
        if isinstance(data, dict):
            return data.get("Volumes", [])
        return data if isinstance(data, list) else []

    async def get_networks(self) -> list[dict[str, Any]]:
        data = await self._get("/networks")
        return data if isinstance(data, list) else data.get("data", [])

    async def get_events(self, since: str = "", until: str = "") -> list[dict[str, Any]]:
        path = "/events"
        params: list[str] = []
        if since:
            params.append(f"since={since}")
        if until:
            params.append(f"until={until}")
        if params:
            path += "?" + "&".join(params)
        data = await self._get(path)
        return data if isinstance(data, list) else []

    async def get_compose_projects(self) -> list[dict[str, Any]]:
        """Get Compose projects via container labels."""
        containers = await self.get_containers(all=True)
        projects: dict[str, dict[str, Any]] = {}
        for c in containers:
            labels = c.get("Labels") or {}
            project = labels.get("com.docker.compose.project")
            if not project:
                continue
            if project not in projects:
                projects[project] = {
                    "name": project,
                    "services": set(),
                    "running": 0,
                    "failed": 0,
                }
            svc = labels.get("com.docker.compose.service", "")
            if svc:
                projects[project]["services"].add(svc)
            state = (c.get("State") or "").lower()
            if state == "running":
                projects[project]["running"] += 1
            elif state in ("exited", "dead"):
                projects[project]["failed"] += 1

        result = []
        for name, info in projects.items():
            svc_count = len(info["services"])
            running = info["running"]
            failed = info["failed"]
            if failed > 0:
                status = "degraded"
            elif running == svc_count:
                status = "healthy"
            else:
                status = "partial"
            result.append({
                "name": name,
                "services": svc_count,
                "running": running,
                "failed": failed,
                "status": status,
            })
        return result

    # ------------------------------------------------------------------ #
    # Sync wrappers for background thread use                              #
    # ------------------------------------------------------------------ #

    def _run_async(self, coro: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=120)
        return asyncio.run(coro)

    def test_connection_sync(self) -> dict[str, Any]:
        return self._run_async(self.test_connection())

    def get_info_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_info())

    def get_version_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_version())

    def get_containers_sync(self, all: bool = True) -> list[dict[str, Any]]:
        return self._run_async(self.get_containers(all=all))

    def get_container_stats_sync(self, container_id: str) -> dict[str, Any]:
        return self._run_async(self.get_container_stats(container_id))

    def get_container_inspect_sync(self, container_id: str) -> dict[str, Any]:
        return self._run_async(self.get_container_inspect(container_id))

    def get_images_sync(self) -> list[dict[str, Any]]:
        return self._run_async(self.get_images())

    def get_volumes_sync(self) -> list[dict[str, Any]]:
        return self._run_async(self.get_volumes())

    def get_networks_sync(self) -> list[dict[str, Any]]:
        return self._run_async(self.get_networks())

    def get_events_sync(self, since: str = "", until: str = "") -> list[dict[str, Any]]:
        return self._run_async(self.get_events(since=since, until=until))

    def get_compose_projects_sync(self) -> list[dict[str, Any]]:
        return self._run_async(self.get_compose_projects())
