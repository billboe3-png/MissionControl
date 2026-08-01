"""
Hyper-V Virtualization Plugin

Production-grade plugin for Hyper-V integration.
Provides background sync, cached data, dashboard widgets,
plugin-scoped REST API, and Event Bus integration.

This plugin wraps the existing Hyper-V provider factory
(HyperVPowerShellProvider / AgentHyperVProvider / MockHyperVProvider)
and caches results into local DB tables for dashboard widgets and REST API.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.events import Event, EventType, event_bus
from app.plugins.installed.hyperv.cache import cache_manager
from app.plugins.installed.hyperv.config import HyperVPluginConfig
from app.plugins.installed.hyperv.models import HyperVHost
from app.plugins.installed.hyperv.routes import router
from app.plugins.installed.hyperv.sync import (
    CheckpointSync,
    NetworkSync,
    VMSync,
    VolumeSync,
)
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.hyperv")


class HyperVPlugin(ServerPluginSDK):
    """Hyper-V virtualization monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._sync_task: asyncio.Task[None] | None = None
        self._plugin_config: HyperVPluginConfig = HyperVPluginConfig(**config)
        self._host_cache: dict[int, int] = {}  # profile_id -> cached_host_id

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        """Initialize: load host configs from IntegrationProfile and cache them."""
        def _load():
            session = SessionLocal()
            try:
                from app.repositories.integration_profile_repository import (
                    IntegrationProfileRepository,
                )
                profiles = IntegrationProfileRepository.get_all_enabled_by_type(
                    session, "hyperv"
                )
                return [
                    {
                        "profile_id": p.id,
                        "name": p.name,
                        "hostname": p.base_url or "unknown",
                        "transport": p.domain or "winrm",
                        "port": 22 if (p.domain or "winrm") == "ssh" else 5985,
                    }
                    for p in profiles
                ]
            finally:
                session.close()

        hosts = await asyncio.to_thread(_load)

        for host in hosts:
            def _upsert_host():
                session = SessionLocal()
                try:
                    existing = session.execute(
                        select(HyperVHost).where(
                            HyperVHost.integration_profile_id == host["profile_id"]
                        )
                    ).scalars().first()

                    if existing:
                        existing.name = host["name"]
                        existing.hostname = host["hostname"]
                        existing.transport = host["transport"]
                        existing.port = host["port"]
                        existing.enabled = True
                        existing.last_sync_at = datetime.now(UTC)
                        existing.status = "healthy"
                    else:
                        new_host = HyperVHost(
                            integration_profile_id=host["profile_id"],
                            name=host["name"],
                            hostname=host["hostname"],
                            transport=host["transport"],
                            port=host["port"],
                            enabled=True,
                            status="healthy",
                        )
                        session.add(new_host)
                        session.commit()
                        existing = new_host

                    return existing.id
                finally:
                    session.close()

            host_id = await asyncio.to_thread(_upsert_host)
            self._host_cache[host["profile_id"]] = host_id

        logger.info(
            "Hyper-V plugin setup: %d host(s) configured", len(self._host_cache)
        )

    async def start(self) -> None:
        """Start background sync task."""
        if self._plugin_config.auto_sync_enabled and self._host_cache:
            self._sync_task = asyncio.create_task(self._background_sync())
            logger.info(
                "Hyper-V background sync started (interval=%ds)",
                self._plugin_config.sync_interval_seconds,
            )

    async def stop(self) -> None:
        """Cancel sync task."""
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Hyper-V plugin stopped")

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def _background_sync(self) -> None:
        """Periodically sync data from all enabled Hyper-V hosts."""
        while True:
            try:
                await self._run_sync_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Hyper-V sync cycle failed")
            await asyncio.sleep(self._plugin_config.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Run one sync cycle for all hosts."""
        def _load_hosts():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(HyperVHost).where(HyperVHost.enabled.is_(True))
                    ).scalars().all()
                )
            finally:
                session.close()

        hosts = await asyncio.to_thread(_load_hosts)

        for host in hosts:
            try:
                await self._sync_host(host)
                logger.debug("Sync completed for host %s", host.name)
            except Exception as exc:
                logger.warning("Sync failed for host %s: %s", host.name, exc)
                await self._mark_host_error(host.id, str(exc)[:500])

        # Publish summary event
        await event_bus.publish(Event(
            type=EventType.PLUGIN_HEALTH_CHANGED,
            data={"plugin": "hyperv", "status": "synced"},
            source="plugin.hyperv",
        ))

    async def _sync_host(self, host: HyperVHost) -> None:
        """Sync all data for a single Hyper-V host."""
        from app.providers.hyperv.provider_factory import get_hyperv_provider

        def _get_provider():
            db = SessionLocal()
            try:
                profile_id = host.integration_profile_id
                if profile_id and profile_id > 0:
                    return get_hyperv_provider(db, profile_id)
                return None
            finally:
                db.close()

        provider = await asyncio.to_thread(_get_provider)
        if provider is None:
            logger.debug("No provider for host %s, skipping sync", host.name)
            return

        vm_sync = VMSync()
        net_sync = NetworkSync()
        vol_sync = VolumeSync()
        cp_sync = CheckpointSync()
        host_id = host.id

        async def _do_sync():
            session = SessionLocal()
            try:
                await vm_sync.sync(session, provider, host_id)
                await net_sync.sync(session, provider, host_id)
                await vol_sync.sync(session, provider, host_id)
                await cp_sync.sync(session, provider, host_id)

                host_row = session.get(HyperVHost, host_id)
                if host_row:
                    host_row.last_sync_at = datetime.now(UTC)
                    host_row.status = "healthy"
                    host_row.last_error = None
                session.commit()
            finally:
                session.close()

        await _do_sync()

    @staticmethod
    async def _mark_host_error(host_id: int, error_msg: str) -> None:
        """Write error state for a host in a background thread."""

        def _write():
            session = SessionLocal()
            try:
                host_row = session.get(HyperVHost, host_id)
                if host_row:
                    host_row.status = "error"
                    host_row.last_error = error_msg
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
                "id": "hyperv-summary",
                "title": "Hyper-V Overview",
                "component": "HyperVSummaryWidget",
                "size": "large",
                "refresh_interval": 60,
            },
            {
                "id": "hyperv-vms-running",
                "title": "Running VMs",
                "component": "HyperVRunningVmsWidget",
                "size": "medium",
                "refresh_interval": 60,
            },
            {
                "id": "hyperv-vms-stopped",
                "title": "Stopped VMs",
                "component": "HyperVStoppedVmsWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "hyperv-checkpoints",
                "title": "Recent Checkpoints",
                "component": "HyperVCheckpointsWidget",
                "size": "medium",
                "refresh_interval": 300,
            },
            {
                "id": "hyperv-hosts",
                "title": "Hosts",
                "component": "HyperVHostsWidget",
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
        if widget_id == "hyperv-summary":
            return cache_manager.get_summary(session)
        if widget_id == "hyperv-vms-running":
            return {"vms": cache_manager.get_vms(session, state="running")}
        if widget_id == "hyperv-vms-stopped":
            return {"vms": cache_manager.get_vms(session, state="stopped")}
        if widget_id == "hyperv-checkpoints":
            return {"checkpoints": cache_manager.get_checkpoints(session)[:10]}
        if widget_id == "hyperv-hosts":
            return {"hosts": cache_manager.get_hosts(session)}
        return {}

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "hyperv-overview",
                "label": "Hyper-V Overview",
                "icon": "server",
                "path": "/plugins/hyperv",
                "group": "Virtualization",
                "order": 10,
            },
            {
                "id": "hyperv-vms",
                "label": "Virtual Machines",
                "icon": "box",
                "path": "/plugins/hyperv/vms",
                "group": "Virtualization",
                "order": 20,
            },
            {
                "id": "hyperv-networks",
                "label": "Virtual Switches",
                "icon": "network",
                "path": "/plugins/hyperv/networks",
                "group": "Virtualization",
                "order": 30,
            },
            {
                "id": "hyperv-volumes",
                "label": "Virtual Hard Disks",
                "icon": "database",
                "path": "/plugins/hyperv/volumes",
                "group": "Virtualization",
                "order": 40,
            },
            {
                "id": "hyperv-checkpoints",
                "label": "Checkpoints",
                "icon": "camera",
                "path": "/plugins/hyperv/checkpoints",
                "group": "Virtualization",
                "order": 50,
            },
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {
                "path": "/api/v1/plugins/hyperv",
                "router": router,
                "summary": "Hyper-V plugin API",
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
                "max_vms": {
                    "type": "integer",
                    "title": "Max VMs to cache",
                    "minimum": 100,
                    "maximum": 10000,
                    "default": 2000,
                },
                "max_networks": {
                    "type": "integer",
                    "title": "Max networks to cache",
                    "minimum": 10,
                    "maximum": 1000,
                    "default": 200,
                },
                "max_volumes": {
                    "type": "integer",
                    "title": "Max volumes to cache",
                    "minimum": 10,
                    "maximum": 5000,
                    "default": 500,
                },
                "max_checkpoints": {
                    "type": "integer",
                    "title": "Max checkpoints to cache",
                    "minimum": 10,
                    "maximum": 5000,
                    "default": 500,
                },
                "cpu_warning_pct": {
                    "type": "number",
                    "title": "CPU warning threshold (%)",
                    "minimum": 50,
                    "maximum": 99,
                    "default": 80.0,
                },
                "cpu_critical_pct": {
                    "type": "number",
                    "title": "CPU critical threshold (%)",
                    "minimum": 80,
                    "maximum": 100,
                    "default": 95.0,
                },
                "memory_warning_pct": {
                    "type": "number",
                    "title": "Memory warning threshold (%)",
                    "minimum": 50,
                    "maximum": 99,
                    "default": 80.0,
                },
                "memory_critical_pct": {
                    "type": "number",
                    "title": "Memory critical threshold (%)",
                    "minimum": 80,
                    "maximum": 100,
                    "default": 95.0,
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self._plugin_config = HyperVPluginConfig(**settings)
        self.config.update(settings)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        def _query():
            session = SessionLocal()
            try:
                host_count = (session.execute(
                    select(func.count(HyperVHost.id))
                )).scalar() or 0
                healthy_count = (session.execute(
                    select(func.count(HyperVHost.id)).where(
                        HyperVHost.status == "healthy"
                    )
                )).scalar() or 0
                return host_count, healthy_count
            finally:
                session.close()

        host_count, healthy_count = await asyncio.to_thread(_query)

        if host_count == 0:
            return {"status": "warning", "message": "No hosts configured"}

        if healthy_count == host_count:
            return {"status": "ok", "hosts": host_count, "healthy": healthy_count}
        if healthy_count > 0:
            return {"status": "degraded", "hosts": host_count, "healthy": healthy_count}
        return {"status": "error", "hosts": host_count, "healthy": 0}
