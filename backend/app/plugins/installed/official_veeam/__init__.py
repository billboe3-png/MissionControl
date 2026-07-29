"""
Veeam Backup & Replication Plugin

Production-grade plugin for Veeam B&R integration.
Provides background sync, cached data, dashboard widgets,
plugin-scoped routes, and Event Bus integration.

All API communication flows through VeeamRESTProvider.
DashboardService remains the only frontend data source.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.db.database import SessionLocal
from app.events import Event, EventType, event_bus
from app.plugins.installed.official_veeam.api import VeeamApiClient
from app.plugins.installed.official_veeam.cache import cache_manager
from app.plugins.installed.official_veeam.config import VeeamPluginConfig
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.plugins.installed.official_veeam.routes import router
from app.plugins.installed.official_veeam.sync import (
    JobSync,
    LicenseSync,
    RepositorySync,
    RestorePointSync,
    ServerSync,
)
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.veeam")


class VeeamPlugin(ServerPluginSDK):
    """Veeam B&R monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._clients: dict[int, VeeamApiClient] = {}
        self._sync_task: asyncio.Task[None] | None = None
        self._plugin_config: VeeamPluginConfig = VeeamPluginConfig(**config)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        """Initialize: load server configs from DB and create API clients."""
        def _load():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(VeeamBackupServer).where(
                            VeeamBackupServer.enabled.is_(True)
                        )
                    ).scalars().all()
                )
            finally:
                session.close()

        servers = await asyncio.to_thread(_load)

        for server in servers:
            if server.encrypted_password:
                try:
                    from app.core.config import get_settings
                    from app.core.security import CredentialCipher
                    cipher = CredentialCipher(
                        get_settings().missioncontrol_secret_key
                    )
                    password = cipher.decrypt(server.encrypted_password)
                except Exception:
                    password = ""
            else:
                password = ""

            client = VeeamApiClient(
                base_url=server.url,
                username=server.username,
                password=password,
                verify_ssl=server.verify_ssl,
                timeout=server.timeout,
            )
            self._clients[server.id] = client

        logger.info(
            "Veeam plugin setup: %d server(s) configured",
            len(self._clients),
        )

    async def start(self) -> None:
        """Start background sync task."""
        if self._plugin_config.auto_sync_enabled and self._clients:
            self._sync_task = asyncio.create_task(self._background_sync())
            logger.info(
                "Veeam background sync started (interval=%ds)",
                self._plugin_config.sync_interval_seconds,
            )

    async def stop(self) -> None:
        """Cancel sync task and close all API clients."""
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        self._clients.clear()
        logger.info("Veeam plugin stopped")

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def _background_sync(self) -> None:
        """Periodically sync data from all enabled Veeam servers."""
        while True:
            try:
                await self._run_sync_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Veeam sync cycle failed")
            await asyncio.sleep(self._plugin_config.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Run one sync cycle for all servers."""
        def _load_servers():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(VeeamBackupServer).where(
                            VeeamBackupServer.enabled.is_(True)
                        )
                    ).scalars().all()
                )
            finally:
                session.close()

        servers = await asyncio.to_thread(_load_servers)

        for server in servers:
            client = self._clients.get(server.id)
            if not client:
                continue
            try:
                await self._sync_server(client, server.id)
                logger.debug("Sync completed for server %s", server.name)

                await event_bus.publish(Event(
                    type=EventType.PLUGIN_HEALTH_CHANGED,
                    data={"plugin": "veeam", "server_id": server.id, "status": "synced"},
                    source="plugin.veeam",
                ))

            except Exception as exc:
                logger.warning(
                    "Sync failed for server %s: %s", server.name, exc,
                )
                await self._mark_server_error(server.id, str(exc)[:500])

                await event_bus.publish(Event(
                    type=EventType.PLUGIN_HEALTH_CHANGED,
                    data={
                        "plugin": "veeam",
                        "server_id": server.id,
                        "status": "sync_failed",
                        "error": str(exc)[:200],
                    },
                    source="plugin.veeam",
                ))

    async def _sync_server(self, client: VeeamApiClient, server_id: int) -> None:
        """Sync all data for a single server."""
        server_sync = ServerSync()
        repo_sync = RepositorySync()
        job_sync = JobSync()
        rp_sync = RestorePointSync()
        lic_sync = LicenseSync()

        def _do_sync():
            session = SessionLocal()
            try:
                server_sync.sync(session, client, server_id)
                repo_sync.sync(session, client, server_id)
                job_sync.sync(session, client, server_id)
                rp_sync.sync(session, client, server_id)
                lic_sync.sync(session, client, server_id)
            finally:
                session.close()

        await asyncio.to_thread(_do_sync)

    @staticmethod
    async def _mark_server_error(server_id: int, error_msg: str) -> None:
        """Write error state for a server in a background thread."""

        def _write():
            session = SessionLocal()
            try:
                server = session.get(VeeamBackupServer, server_id)
                if server:
                    server.status = "error"
                    server.last_error = error_msg
                    server.last_sync_at = datetime.now(UTC)
                session.commit()
            finally:
                session.close()

        await asyncio.to_thread(_write)

    # ------------------------------------------------------------------ #
    # Dashboard                                                           #
    # ------------------------------------------------------------------ #

    async def get_dashboard_widgets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "veeam-summary",
                "title": "Veeam Backup Overview",
                "component": "VeeamSummaryWidget",
                "size": "large",
                "refresh_interval": 120,
            },
            {
                "id": "veeam-failed-jobs",
                "title": "Failed Jobs",
                "component": "VeeamFailedJobsWidget",
                "size": "medium",
                "refresh_interval": 60,
            },
            {
                "id": "veeam-repository-capacity",
                "title": "Repository Capacity",
                "component": "VeeamRepositoryCapacityWidget",
                "size": "medium",
                "refresh_interval": 300,
            },
            {
                "id": "veeam-jobs-by-type",
                "title": "Jobs by Type",
                "component": "VeeamJobsByTypeWidget",
                "size": "small",
                "refresh_interval": 120,
            },
            {
                "id": "veeam-repo-health",
                "title": "Repository Health",
                "component": "VeeamRepoHealthWidget",
                "size": "medium",
                "refresh_interval": 300,
            },
            {
                "id": "veeam-restore-points",
                "title": "Restore Points",
                "component": "VeeamRestorePointsWidget",
                "size": "small",
                "refresh_interval": 600,
            },
            {
                "id": "veeam-license",
                "title": "License Status",
                "component": "VeeamLicenseWidget",
                "size": "small",
                "refresh_interval": 600,
            },
            {
                "id": "veeam-servers",
                "title": "Backup Servers",
                "component": "VeeamServersWidget",
                "size": "small",
                "refresh_interval": 120,
            },
        ]

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        def _query():
            session = SessionLocal()
            try:
                return self._fetch_widget_data(widget_id, session)
            finally:
                session.close()

        return await asyncio.to_thread(_query)

    def _fetch_widget_data(
        self, widget_id: str, session: Any,
    ) -> dict[str, Any]:
        """Fetch widget data from cache (runs in thread)."""
        if widget_id == "veeam-summary":
            return cache_manager.get_summary(session)
        if widget_id == "veeam-failed-jobs":
            jobs = cache_manager.get_jobs(session)
            failed = [
                j for j in jobs
                if j.get("last_result", "").lower() in ("failed", "warning")
                or j.get("status", "").lower() == "failed"
            ]
            return {"jobs": failed[:20], "total_failed": len(failed)}
        if widget_id == "veeam-repository-capacity":
            repos = cache_manager.get_repositories(session)
            total = sum(r["total_space_bytes"] for r in repos)
            free = sum(r["free_space_bytes"] for r in repos)
            return {
                "repositories": repos,
                "total_bytes": total,
                "free_bytes": free,
                "used_bytes": total - free,
            }
        if widget_id == "veeam-jobs-by-type":
            return {"jobs_by_type": cache_manager.get_jobs_by_type(session)}
        if widget_id == "veeam-repo-health":
            return {"repos": cache_manager.get_repo_health(session)}
        if widget_id == "veeam-restore-points":
            rps = cache_manager.get_restore_points(session)
            return {"restore_points": rps[:50], "total_count": len(rps)}
        if widget_id == "veeam-license":
            lics = cache_manager.get_license(session)
            return {"licenses": lics}
        if widget_id == "veeam-servers":
            return {"servers": cache_manager.get_servers(session)}
        return {}

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "veeam-dashboard",
                "label": "Veeam Dashboard",
                "icon": "database",
                "path": "/plugins/veeam",
                "group": "Backup & Recovery",
                "order": 10,
            },
            {
                "id": "veeam-jobs",
                "label": "Jobs",
                "icon": "play-circle",
                "path": "/plugins/veeam/jobs",
                "group": "Backup & Recovery",
                "order": 20,
            },
            {
                "id": "veeam-repositories",
                "label": "Repositories",
                "icon": "hard-drive",
                "path": "/plugins/veeam/repositories",
                "group": "Backup & Recovery",
                "order": 30,
            },
            {
                "id": "veeam-restore-points",
                "label": "Restore Points",
                "icon": "clock",
                "path": "/plugins/veeam/restore-points",
                "group": "Backup & Recovery",
                "order": 40,
            },
            {
                "id": "veeam-servers",
                "label": "Backup Servers",
                "icon": "server",
                "path": "/plugins/veeam/servers",
                "group": "Backup & Recovery",
                "order": 50,
            },
            {
                "id": "veeam-health",
                "label": "Health",
                "icon": "heart-pulse",
                "path": "/plugins/veeam/health",
                "group": "Backup & Recovery",
                "order": 60,
            },
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {
                "path": "/api/v1/plugins/veeam",
                "router": router,
                "summary": "Veeam plugin API",
            }
        ]

    # ------------------------------------------------------------------ #
    # Settings                                                            #
    # ------------------------------------------------------------------ #

    async def get_settings_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "auto_sync_enabled": {
                    "type": "boolean",
                    "title": "Auto-sync",
                    "default": True,
                },
                "sync_interval_seconds": {
                    "type": "integer",
                    "title": "Sync interval (seconds)",
                    "minimum": 60,
                    "maximum": 3600,
                    "default": 300,
                },
                "max_jobs": {
                    "type": "integer",
                    "title": "Max jobs to cache",
                    "minimum": 50,
                    "maximum": 5000,
                    "default": 500,
                },
                "max_sessions": {
                    "type": "integer",
                    "title": "Max sessions to cache",
                    "minimum": 50,
                    "maximum": 5000,
                    "default": 500,
                },
                "job_retention_days": {
                    "type": "integer",
                    "title": "Job retention (days)",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                },
                "event_retention_days": {
                    "type": "integer",
                    "title": "Event retention (days)",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                },
                "repo_capacity_warning_pct": {
                    "type": "number",
                    "title": "Repository capacity warning (%)",
                    "minimum": 50,
                    "maximum": 99,
                    "default": 80,
                },
                "repo_capacity_critical_pct": {
                    "type": "number",
                    "title": "Repository capacity critical (%)",
                    "minimum": 80,
                    "maximum": 100,
                    "default": 95,
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self._plugin_config = VeeamPluginConfig(**settings)
        self.config.update(settings)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        if not self._clients:
            return {"status": "warning", "message": "No servers configured"}

        healthy = 0
        errors: list[str] = []
        for _server_id, client in self._clients.items():
            try:
                result = await client.test_connection()
                if result.get("healthy") or result.get("success"):
                    healthy += 1
                else:
                    errors.append(result.get("error", "unhealthy"))
            except Exception as exc:
                errors.append(str(exc)[:200])

        total = len(self._clients)
        if healthy == total:
            return {"status": "ok", "servers": total, "healthy": healthy}
        if healthy > 0:
            return {
                "status": "degraded",
                "servers": total,
                "healthy": healthy,
                "errors": errors,
            }
        return {
            "status": "error",
            "servers": total,
            "healthy": 0,
            "errors": errors,
        }
