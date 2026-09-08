"""
D-Link DGS-1210 Plugin

Manages registered D-Link DGS-1210 switches via SSH/Telnet and the Web UI.
Switches are stored in dlink_switches with encrypted credentials; a
background task refreshes status/facts and publishes state transitions
onto the event bus.
"""

import asyncio
import contextlib
import logging
from typing import Any

from app.db.database import SessionLocal
from app.plugins.installed.official_dlink.config import DLinkPluginConfig
from app.plugins.installed.official_dlink.repository import repository
from app.plugins.installed.official_dlink.routes import router
from app.plugins.installed.official_dlink.service import dlink_service
from app.plugins.installed.official_dlink.sync import sync_service
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.dlink")


class DLinkPlugin(ServerPluginSDK):
    """D-Link DGS-1210 monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._plugin_config = DLinkPluginConfig()
        self._sync_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        logger.info("D-Link plugin setup")

    async def start(self) -> None:
        if not self._plugin_config.auto_sync_enabled:
            logger.info("D-Link background sync disabled by configuration")
            return
        self._sync_task = asyncio.create_task(self._background_sync())
        logger.info(
            "D-Link background sync started (interval=%ds)",
            self._plugin_config.sync_interval_seconds,
        )

    async def stop(self) -> None:
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task
        self._sync_task = None
        logger.info("D-Link plugin stopped")

    async def _background_sync(self) -> None:
        interval = self._plugin_config.sync_interval_seconds
        while True:
            try:
                await sync_service._sync_all_switches()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("D-Link sync cycle failed")
            await asyncio.sleep(interval)

    # ------------------------------------------------------------------ #
    # Dashboard                                                           #
    # ------------------------------------------------------------------ #

    async def get_dashboard_widgets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "dlink-switches",
                "title": "D-Link Switches",
                "component": "DLinkSwitchesWidget",
                "size": "medium",
                "refresh_interval": 60,
            }
        ]

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        if widget_id != "dlink-switches":
            return {}

        session = SessionLocal()
        try:
            switches = repository.list_switches(session)
            online = sum(1 for s in switches if s.status == "online")
            return {
                "status": "ok" if online else ("empty" if not switches else "warning"),
                "total": len(switches),
                "online": online,
                "switches": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "host": s.host,
                        "status": s.status,
                        "version": s.firmware_version,
                        "model": s.model_name,
                    }
                    for s in switches[:10]
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
                "id": "dlink-overview",
                "label": "D-Link",
                "icon": "network",
                "path": "/dlink",
                "group": "Infrastructure",
                "order": 12,
            }
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {"path": "/api/v1/plugins/dlink", "router": router},
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
            **{k: v for k, v in settings.items() if k in DLinkPluginConfig.model_fields},
        }
        self._plugin_config = DLinkPluginConfig(**updated)
        self.config.update(updated)
        await self.on_config_changed(previous)

    async def on_config_changed(self, previous: dict[str, Any]) -> None:
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
            switches = repository.list_switches(session)
            enabled = [s for s in switches if s.enabled]
            online = sum(1 for s in enabled if s.status == "online")
            if not switches:
                return {
                    "status": "warning",
                    "message": "No switches configured",
                    "version": self.version,
                    "plugin": self.slug,
                }
            return {
                "status": "ok" if online > 0 else "warning",
                "total": len(switches),
                "enabled": len(enabled),
                "online": online,
                "version": self.version,
                "plugin": self.slug,
            }
        finally:
            session.close()


# Export for backward compatibility
from .config import DLinkPluginConfig, get_plugin_config
from .models import (
    DLinkSwitch,
    DLinkRemoteTarget,
    DLinkMacEntry,
    DLinkVlan,
    DLinkPortVlan,
)
from .repository import repository, DLinkRepository
from .service import dlink_service, DLinkService
from .relay import execute_plugin_command, rest_api_call, start_webui_stream
from .webui_manager import webui_manager, WebUIManager
from .sync import sync_service, DLinkSync
from .cache import cache_manager, DLinkCacheManager
from .routes import router

__all__ = [
    "DLinkPlugin",
    "DLinkPluginConfig",
    "get_plugin_config",
    "DLinkSwitch",
    "DLinkRemoteTarget",
    "DLinkMacEntry",
    "DLinkVlan",
    "DLinkPortVlan",
    "repository",
    "DLinkRepository",
    "dlink_service",
    "DLinkService",
    "execute_plugin_command",
    "rest_api_call",
    "start_webui_stream",
    "webui_manager",
    "WebUIManager",
    "sync_service",
    "DLinkSync",
    "cache_manager",
    "DLinkCacheManager",
    "router",
]