"""
UniFi Plugin API Client

Async HTTP client for UniFi Site Manager and local controllers.
Handles authentication via API token and data retrieval.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any

import httpx

logger = logging.getLogger("plugin.unifi.api")


class UniFiApiClient:
    """Async UniFi REST API client."""

    SITE_MANAGER_URL = "https://unifi.ui.com"

    def __init__(
        self,
        url: str,
        api_key: str,
        verify_ssl: bool = True,
        timeout: int = 30,
        retries: int = 3,
        controller_type: str = "cloud",
    ) -> None:
        self._url = url.rstrip("/")
        self._api_key = api_key
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._retries = retries
        self._controller_type = controller_type
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self._verify_ssl,
                timeout=httpx.Timeout(self._timeout),
                headers={"x-api-key": self._api_key},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _get(self, path: str) -> Any:
        """Execute a GET request with retries."""
        client = await self._get_client()
        url = f"{self._url}{path}"

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
            f"UniFi API call '{path}' failed after {self._retries} attempts: {last_error}"
        )

    async def test_connection(self) -> dict[str, Any]:
        try:
            data = await self._get("/api/self")
            return {"connected": True, "data": data}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    async def get_organizations(self) -> list[dict[str, Any]]:
        data = await self._get("/api/orgs")
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_sites(self, org_id: str = "") -> list[dict[str, Any]]:
        path = "/api/sites"
        if org_id:
            path = f"/api/orgs/{org_id}/sites"
        data = await self._get(path)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_devices(self, site_id: str = "") -> list[dict[str, Any]]:
        path = f"/api/sites/{site_id}/devices" if site_id else "/api/devices"
        data = await self._get(path)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_clients(self, site_id: str = "") -> list[dict[str, Any]]:
        path = f"/api/sites/{site_id}/clients" if site_id else "/api/clients"
        data = await self._get(path)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_alerts(self, site_id: str = "") -> list[dict[str, Any]]:
        path = f"/api/sites/{site_id}/alerts" if site_id else "/api/alerts"
        data = await self._get(path)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_networks(self, site_id: str = "") -> list[dict[str, Any]]:
        path = f"/api/sites/{site_id}/conf/adv" if site_id else "/api/networks"
        data = await self._get(path)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_health(self, site_id: str = "") -> dict[str, Any]:
        path = f"/api/sites/{site_id}/health" if site_id else "/api/health"
        return await self._get(path)

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

    def get_sites_sync(self, org_id: str = "") -> list[dict[str, Any]]:
        return self._run_async(self.get_sites(org_id))

    def get_devices_sync(self, site_id: str = "") -> list[dict[str, Any]]:
        return self._run_async(self.get_devices(site_id))

    def get_clients_sync(self, site_id: str = "") -> list[dict[str, Any]]:
        return self._run_async(self.get_clients(site_id))

    def get_alerts_sync(self, site_id: str = "") -> list[dict[str, Any]]:
        return self._run_async(self.get_alerts(site_id))

    def get_networks_sync(self, site_id: str = "") -> list[dict[str, Any]]:
        return self._run_async(self.get_networks(site_id))
