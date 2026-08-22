"""
Docker & Container Monitoring Plugin

Production-grade plugin for Docker Engine API integration.
Provides background sync, cached data, dashboard widgets,
plugin-scoped routes, and Event Bus integration.

All API communication flows through DockerApiClient.
DashboardService remains the only frontend data source.
"""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.db.database import SessionLocal
from app.events import Event, EventType, event_bus
from app.plugins.installed.official_docker.api import DockerApiClient
from app.plugins.installed.official_docker.cache import cache_manager
from app.plugins.installed.official_docker.config import DockerPluginConfig
from app.plugins.installed.official_docker.models import DockerHost
from app.plugins.installed.official_docker.routes import router
from app.plugins.installed.official_docker.sync import (
    ComposeSync,
    ContainerSync,
    HostSync,
    ImageSync,
    NetworkSync,
    VolumeSync,
)
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.docker")


class DockerPlugin(ServerPluginSDK):
    """Docker & Container monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._clients: dict[int, DockerApiClient] = {}
        self._sync_task: asyncio.Task[None] | None = None
        self._plugin_config: DockerPluginConfig = DockerPluginConfig(**config)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        """Initialize: load host configs from DB and create API clients."""
        def _load():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(DockerHost).where(DockerHost.online.is_(True))
                    ).scalars().all()
                )
            finally:
                session.close()

        hosts = await asyncio.to_thread(_load)

        for host in hosts:
            client = DockerApiClient(
                host=host.hostname,
                tls=False,
                timeout=30,
                retries=3,
            )
            self._clients[host.id] = client

        logger.info(
            "Docker plugin setup: %d host(s) configured",
            len(self._clients),
        )

    async def start(self) -> None:
        """Start background sync task."""
        if self._plugin_config.auto_sync_enabled and self._clients:
            self._sync_task = asyncio.create_task(self._background_sync())
            logger.info(
                "Docker background sync started (interval=%ds)",
                self._plugin_config.sync_interval_seconds,
            )

    async def stop(self) -> None:
        """Cancel sync task and close all API clients."""
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        logger.info("Docker plugin stopped")

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def _background_sync(self) -> None:
        """Periodically sync data from all enabled Docker hosts."""
        while True:
            try:
                await self._run_sync_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Docker sync cycle failed")
            await asyncio.sleep(self._plugin_config.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Run one sync cycle for all hosts."""
        def _load_hosts():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(DockerHost).where(DockerHost.online.is_(True))
                    ).scalars().all()
                )
            finally:
                session.close()

        hosts = await asyncio.to_thread(_load_hosts)

        for host in hosts:
            client = self._clients.get(host.id)
            if not client:
                continue
            try:
                await self._sync_host(client, host.id)
                logger.debug("Sync completed for host %s", host.name)

                await event_bus.publish(Event(
                    type=EventType.PLUGIN_HEALTH_CHANGED,
                    data={"plugin": "docker", "host_id": host.id, "status": "synced"},
                    source="plugin.docker",
                ))

            except Exception as exc:
                logger.warning("Sync failed for host %s: %s", host.name, exc)
                await self._mark_host_error(host.id, str(exc)[:500])

                await event_bus.publish(Event(
                    type=EventType.PLUGIN_HEALTH_CHANGED,
                    data={
                        "plugin": "docker",
                        "host_id": host.id,
                        "status": "sync_failed",
                        "error": str(exc)[:200],
                    },
                    source="plugin.docker",
                ))

    async def _sync_host(self, client: DockerApiClient, host_id: int) -> None:
        """Sync all data for a single Docker host."""
        host_sync = HostSync()
        container_sync = ContainerSync()
        image_sync = ImageSync()
        volume_sync = VolumeSync()
        network_sync = NetworkSync()
        compose_sync = ComposeSync()

        def _do_sync():
            session = SessionLocal()
            try:
                host_sync.sync(session, client, host_id)
                container_sync.sync(session, client, host_id)
                image_sync.sync(session, client, host_id)
                volume_sync.sync(session, client, host_id)
                network_sync.sync(session, client, host_id)
                compose_sync.sync(session, client, host_id)
            finally:
                session.close()

        await asyncio.to_thread(_do_sync)

    @staticmethod
    async def _mark_host_error(host_id: int, error_msg: str) -> None:
        """Write error state for a host in a background thread."""

        def _write():
            session = SessionLocal()
            try:
                host = session.get(DockerHost, host_id)
                if host:
                    host.online = False
                    host.last_error = error_msg
                    host.last_sync_at = datetime.now(UTC)
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
                "id": "docker-summary",
                "title": "Docker Overview",
                "component": "DockerSummaryWidget",
                "size": "large",
                "refresh_interval": 60,
            },
            {
                "id": "docker-hosts",
                "title": "Docker Hosts",
                "component": "DockerHostsWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "docker-containers-running",
                "title": "Running Containers",
                "component": "DockerRunningContainersWidget",
                "size": "medium",
                "refresh_interval": 60,
            },
            {
                "id": "docker-containers-stopped",
                "title": "Stopped Containers",
                "component": "DockerStoppedContainersWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "docker-containers-unhealthy",
                "title": "Unhealthy Containers",
                "component": "DockerUnhealthyContainersWidget",
                "size": "medium",
                "refresh_interval": 60,
            },
            {
                "id": "docker-cpu-usage",
                "title": "CPU Usage",
                "component": "DockerCpuUsageWidget",
                "size": "small",
                "refresh_interval": 60,
            },
            {
                "id": "docker-memory-usage",
                "title": "Memory Usage",
                "component": "DockerMemoryUsageWidget",
                "size": "small",
                "refresh_interval": 60,
            },
            {
                "id": "docker-images",
                "title": "Images",
                "component": "DockerImagesWidget",
                "size": "small",
                "refresh_interval": 300,
            },
            {
                "id": "docker-volumes",
                "title": "Volumes",
                "component": "DockerVolumesWidget",
                "size": "small",
                "refresh_interval": 300,
            },
            {
                "id": "docker-compose",
                "title": "Compose Health",
                "component": "DockerComposeHealthWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "docker-restarting",
                "title": "Restarting Containers",
                "component": "DockerRestartingWidget",
                "size": "small",
                "refresh_interval": 60,
            },
            {
                "id": "docker-version",
                "title": "Docker Version",
                "component": "DockerVersionWidget",
                "size": "small",
                "refresh_interval": 600,
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
        if widget_id == "docker-summary":
            return cache_manager.get_summary(session)
        if widget_id == "docker-hosts":
            return {"hosts": cache_manager.get_hosts(session)}
        if widget_id == "docker-containers-running":
            return {"containers": cache_manager.get_containers(session, state="running")}
        if widget_id == "docker-containers-stopped":
            return {"containers": cache_manager.get_containers(session, state="exited")}
        if widget_id == "docker-containers-unhealthy":
            return {"containers": cache_manager.get_containers(session, state="running"),
                    "health": cache_manager.get_container_health(session)}
        if widget_id == "docker-cpu-usage":
            return cache_manager.get_resource_usage(session)
        if widget_id == "docker-memory-usage":
            return cache_manager.get_resource_usage(session)
        if widget_id == "docker-images":
            images = cache_manager.get_images(session)
            return {"images": images[:100], "total_count": len(images)}
        if widget_id == "docker-volumes":
            return {"volumes": cache_manager.get_volumes(session)}
        if widget_id == "docker-compose":
            return {"stacks": cache_manager.get_compose(session)}
        if widget_id == "docker-restarting":
            return {"containers": cache_manager.get_containers(session, state="restarting")}
        if widget_id == "docker-version":
            hosts = cache_manager.get_hosts(session)
            return {"hosts": hosts}
        return {}

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "docker-dashboard",
                "label": "Docker Dashboard",
                "icon": "container",
                "path": "/plugins/docker",
                "group": "Containers",
                "order": 10,
            },
            {
                "id": "docker-containers",
                "label": "Containers",
                "icon": "box",
                "path": "/plugins/docker/containers",
                "group": "Containers",
                "order": 20,
            },
            {
                "id": "docker-images",
                "label": "Images",
                "icon": "layers",
                "path": "/plugins/docker/images",
                "group": "Containers",
                "order": 30,
            },
            {
                "id": "docker-volumes",
                "label": "Volumes",
                "icon": "database",
                "path": "/plugins/docker/volumes",
                "group": "Containers",
                "order": 40,
            },
            {
                "id": "docker-networks",
                "label": "Networks",
                "icon": "network",
                "path": "/plugins/docker/networks",
                "group": "Containers",
                "order": 50,
            },
            {
                "id": "docker-compose",
                "label": "Compose",
                "icon": "stack",
                "path": "/plugins/docker/compose",
                "group": "Containers",
                "order": 60,
            },
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {
                "path": "/api/v1/plugins/docker",
                "router": router,
                "summary": "Docker plugin API",
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
                    "minimum": 30,
                    "maximum": 3600,
                    "default": 120,
                },
                "max_containers": {
                    "type": "integer",
                    "title": "Max containers to cache",
                    "minimum": 100,
                    "maximum": 10000,
                    "default": 2000,
                },
                "max_images": {
                    "type": "integer",
                    "title": "Max images to cache",
                    "minimum": 10,
                    "maximum": 5000,
                    "default": 500,
                },
                "max_volumes": {
                    "type": "integer",
                    "title": "Max volumes to cache",
                    "minimum": 10,
                    "maximum": 5000,
                    "default": 500,
                },
                "max_networks": {
                    "type": "integer",
                    "title": "Max networks to cache",
                    "minimum": 5,
                    "maximum": 1000,
                    "default": 200,
                },
                "cpu_warning_pct": {
                    "type": "number",
                    "title": "CPU warning threshold (%)",
                    "minimum": 50,
                    "maximum": 99,
                    "default": 80,
                },
                "cpu_critical_pct": {
                    "type": "number",
                    "title": "CPU critical threshold (%)",
                    "minimum": 80,
                    "maximum": 100,
                    "default": 95,
                },
                "memory_warning_pct": {
                    "type": "number",
                    "title": "Memory warning threshold (%)",
                    "minimum": 50,
                    "maximum": 99,
                    "default": 80,
                },
                "memory_critical_pct": {
                    "type": "number",
                    "title": "Memory critical threshold (%)",
                    "minimum": 80,
                    "maximum": 100,
                    "default": 95,
                },
                "disk_warning_pct": {
                    "type": "number",
                    "title": "Disk warning threshold (%)",
                    "minimum": 50,
                    "maximum": 99,
                    "default": 80,
                },
                "disk_critical_pct": {
                    "type": "number",
                    "title": "Disk critical threshold (%)",
                    "minimum": 80,
                    "maximum": 100,
                    "default": 95,
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self._plugin_config = DockerPluginConfig(**settings)
        self.config.update(settings)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        if not self._clients:
            return {"status": "warning", "message": "No Docker hosts configured"}

        healthy = 0
        errors: list[str] = []
        for _host_id, client in self._clients.items():
            try:
                result = await client.test_connection()
                if result.get("healthy"):
                    healthy += 1
                else:
                    errors.append(result.get("error", "unreachable"))
            except Exception as exc:
                errors.append(str(exc)[:200])

        total = len(self._clients)
        if healthy == total:
            return {"status": "ok", "hosts": total, "healthy": healthy}
        if healthy > 0:
            return {
                "status": "degraded",
                "hosts": total,
                "healthy": healthy,
                "errors": errors,
            }
        return {
            "status": "error",
            "hosts": total,
            "healthy": 0,
            "errors": errors,
        }
