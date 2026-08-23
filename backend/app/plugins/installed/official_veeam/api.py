"""
Veeam Plugin API Client

Wraps the plugin-native VeeamServerProvider to provide sync/async methods
for the plugin's background sync and route handlers.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any

from app.plugins.installed.official_veeam.provider import (
    VeeamServerProvider,
    build_server_provider,
)

logger = logging.getLogger("plugin.veeam.api")


class VeeamApiClient:
    """Wrapper around VeeamServerProvider for plugin use."""

    def __init__(self, provider: VeeamServerProvider) -> None:
        self._provider = provider

    @classmethod
    def from_server(cls, db: Any, server: Any) -> "VeeamApiClient":
        """Build a client around the capability-routed provider for a server row."""
        return cls(build_server_provider(db, server))

    async def test_connection(self) -> dict[str, Any]:
        return await self._provider.get_health()

    async def get_summary(self) -> dict[str, Any]:
        return await self._provider.get_summary()

    async def get_jobs(self) -> dict[str, Any]:
        return await self._provider.get_jobs()

    async def get_job_detail(self, job_id: str) -> dict[str, Any]:
        return await self._provider.get_job_detail(job_id)

    async def get_sessions(self) -> dict[str, Any]:
        return await self._provider.get_sessions()

    async def get_repositories(self) -> dict[str, Any]:
        return await self._provider.get_repositories()

    async def get_managed_servers(self) -> dict[str, Any]:
        return await self._provider.get_managed_servers()

    async def get_restore_points(self, vm_id: str | None = None) -> dict[str, Any]:
        return await self._provider.get_restore_points(vm_id)

    async def get_license(self) -> dict[str, Any]:
        return await self._provider.get_license()

    async def get_capacity_tier(self) -> dict[str, Any]:
        return await self._provider.get_capacity_tier()

    async def start_job(self, job_id: str) -> dict[str, Any]:
        return await self._provider.start_job(job_id)

    async def stop_job(self, job_id: str) -> dict[str, Any]:
        return await self._provider.stop_job(job_id)

    # ------------------------------------------------------------------ #
    # Sync wrappers for background thread use                              #
    # ------------------------------------------------------------------ #

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine from a sync context."""
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

    def get_summary_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_summary())

    def get_jobs_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_jobs())

    def get_repositories_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_repositories())

    def get_managed_servers_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_managed_servers())

    def get_restore_points_sync(self, vm_id: str | None = None) -> dict[str, Any]:
        return self._run_async(self.get_restore_points(vm_id))

    def get_license_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_license())

    def get_capacity_tier_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_capacity_tier())

    def get_sessions_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_sessions())
