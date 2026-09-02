"""
MikroTik RouterOS Plugin

Manages registered RouterOS devices via SSH, Telnet, and the REST API.
Servers are stored in mikrotik_servers with encrypted credentials; a
background task refreshes status/facts and publishes state transitions
onto the event bus.
"""

import asyncio
import contextlib
import logging
from typing import Any

from app.db.database import SessionLocal
from app.plugins.installed.official_mikrotik.config import MikroTikPluginConfig
from app.plugins.installed.official_mikrotik.repository import MikroTikRepository
from app.plugins.installed.official_mikrotik.routes import router
from app.plugins.installed.official_mikrotik.config_routes import router as config_router
from app.plugins.installed.official_mikrotik.service import mikrotik_service
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.mikrotik")


class MikroTikPlugin(ServerPluginSDK):
    """MikroTik RouterOS monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._plugin_config = MikroTikPluginConfig()
        self._sync_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        logger.info("MikroTik plugin setup")

    async def start(self) -> None:
        if not self._plugin_config.auto_sync_enabled:
            logger.info("MikroTik background sync disabled by configuration")
            return
        self._sync_task = asyncio.create_task(self._background_sync())
        logger.info(
            "MikroTik background sync started (interval=%ds)",
            self._plugin_config.sync_interval_seconds,
        )

    async def stop(self) -> None:
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task
        self._sync_task = None
        logger.info("MikroTik plugin stopped")

    async def _background_sync(self) -> None:
        interval = self._plugin_config.sync_interval_seconds
        while True:
            try:
                session = SessionLocal()
                try:
                    await mikrotik_service.sync_all(session)
                finally:
                    session.close()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("MikroTik sync cycle failed")
            await asyncio.sleep(interval)

    # ------------------------------------------------------------------ #
    # Dashboard                                                           #
    # ------------------------------------------------------------------ #

    async def get_dashboard_widgets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "mikrotik-interfaces",
                "title": "MikroTik Interfaces",
                "component": "MikroTikInterfacesWidget",
                "size": "medium",
                "refresh_interval": 60,
            }
        ]

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        if widget_id != "mikrotik-interfaces":
            return {}

        session = SessionLocal()
        try:
            servers = MikroTikRepository.list_servers(session)
            online = sum(1 for s in servers if s.status == "online")
            return {
                "status": "ok" if online else ("empty" if not servers else "warning"),
                "total": len(servers),
                "online": online,
                "servers": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "host": s.host,
                        "status": s.status,
                        "version": s.version,
                        "board_name": s.board_name,
                    }
                    for s in servers[:10]
                ],
            }
        finally:
            session.close()

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "mikrotik-overview",
                "label": "MikroTik",
                "icon": "network",
                "path": "/mikrotik",
                "group": "Infrastructure",
                "order": 11,
            }
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {"path": "/api/v1/plugins/mikrotik", "router": router},
            {"path": "/api/v1/plugins/mikrotik", "router": config_router},
        ]

    # ------------------------------------------------------------------ #
    # Settings                                                            #
    # ------------------------------------------------------------------ #

    async def get_settings_schema(self) -> dict[str, Any]:
        return self._plugin_config.model_json_schema()

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        previous = self._plugin_config.model_dump()
        updated = {
            **previous,
            **{k: v for k, v in settings.items() if k in MikroTikPluginConfig.model_fields},
        }
        self._plugin_config = MikroTikPluginConfig(**updated)
        self.config.update(updated)
        await self.on_config_changed(previous)

    async def on_config_changed(self, previous: dict[str, Any]) -> None:
        """Restart the sync loop when scheduling settings change."""
        settings_changed = (
            previous.get("auto_sync_enabled") != self._plugin_config.auto_sync_enabled
            or previous.get("sync_interval_seconds") != self._plugin_config.sync_interval_seconds
        )
        if not settings_changed:
            return
        await self.stop()
        await self.start()

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        session = SessionLocal()
        try:
            servers = MikroTikRepository.list_servers(session)
            enabled = [s for s in servers if s.enabled]
            online = sum(1 for s in enabled if s.status == "online")
            if not servers:
                return {
                    "status": "warning",
                    "message": "No servers configured",
                    "version": self.version,
                    "plugin": self.slug,
                }
            return {
                "status": "ok" if online > 0 else "warning",
                "total": len(servers),
                "enabled": len(enabled),
                "online": online,
                "version": self.version,
                "plugin": self.slug,
            }
        finally:
            session.close()
