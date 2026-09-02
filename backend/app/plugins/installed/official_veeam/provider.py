"""
Veeam Plugin Server Provider

Minimal per-server provider wrapper around VeeamApiClient.
Provides capability-based health resolution for community (agent-relayed)
servers so the Connection badge reflects db_available.
"""

import logging
from typing import Any

from app.plugins.installed.official_veeam.models import VeeamBackupServer

logger = logging.getLogger("plugin.veeam.provider")


def _get_veeam_api_client() -> type:
    """Late import to avoid circular import."""
    from app.plugins.installed.official_veeam.api import VeeamApiClient
    return VeeamApiClient


def _build_client(db: Any, server: VeeamBackupServer) -> "VeeamApiClient":
    VeeamApiClient = _get_veeam_api_client()
    return VeeamApiClient.from_server(db, server)


class VeeamServerProvider:
    """Per-server provider delegating to VeeamApiClient."""

    def __init__(self, db: Any, server: VeeamBackupServer) -> None:
        self._db = db
        self.server = server
        self._client = _build_client(db, server)

    async def _get_client(self) -> "VeeamApiClient":
        return self._client

    async def get_summary(self, **kwargs) -> dict[str, Any]:
        return await self._client.get_summary()

    async def test_connection(self) -> dict[str, Any]:
        return await self._client.test_connection()

    async def get_health(self) -> dict[str, Any]:
        result = await self._client.test_connection()
        if self.server.edition == "community" and isinstance(result, dict):
            result["healthy"] = bool(
                result.get("rest_available")
                or result.get("powershell_available")
                or result.get("db_available")
            )
        return result

    async def get_jobs(self) -> dict[str, Any]:
        return await self._client.get_jobs()

    async def get_job_detail(self, job_id: str) -> dict[str, Any]:
        return await self._client.get_job_detail(job_id)

    async def get_sessions(self) -> dict[str, Any]:
        return await self._client.get_sessions()

    async def get_repositories(self) -> dict[str, Any]:
        return await self._client.get_repositories()

    async def get_managed_servers(self) -> dict[str, Any]:
        return await self._client.get_managed_servers()

    async def get_restore_points(self, vm_id: str | None = None) -> dict[str, Any]:
        return await self._client.get_restore_points(vm_id)

    async def get_license(self) -> dict[str, Any]:
        return await self._client.get_license()

    async def get_capacity_tier(self) -> dict[str, Any]:
        return await self._client.get_capacity_tier()

    async def get_job_stats(self) -> dict[str, Any]:
        return await self._client.get_job_stats()

    async def get_session_stats(self) -> dict[str, Any]:
        return await self._client.get_session_stats()

    async def get_job_stats_daily(self, days: int = 7) -> dict[str, Any]:
        return await self._client.get_job_stats_daily(days)

    async def start_job(self, job_id: str) -> dict[str, Any]:
        return await self._client.start_job(job_id)

    async def stop_job(self, job_id: str) -> dict[str, Any]:
        return await self._client.stop_job(job_id)


def build_server_provider(db: Any, server: VeeamBackupServer) -> VeeamServerProvider:
    return VeeamServerProvider(db=db, server=server)
