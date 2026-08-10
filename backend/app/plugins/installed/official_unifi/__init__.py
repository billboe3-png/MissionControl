"""
UniFi Site Manager Plugin

Production-grade plugin for Ubiquiti UniFi integration.
Provides background sync, cached data, dashboard widgets,
plugin-scoped routes, and Event Bus integration.

All API communication flows through UniFiApiClient.
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
from app.plugins.installed.official_unifi.api import UniFiApiClient
from app.plugins.installed.official_unifi.cache import cache_manager
from app.plugins.installed.official_unifi.config import UniFiPluginConfig
from app.plugins.installed.official_unifi.models import UniFiController
from app.plugins.installed.official_unifi.routes import router
from app.plugins.installed.official_unifi.sync import (
    AlertSync,
    ClientSync,
    ControllerSync,
    DeviceSync,
    NetworkSync,
    SiteSync,
)
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.unifi")


class UniFiPlugin(ServerPluginSDK):
    """UniFi Site Manager monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._clients: dict[int, UniFiApiClient] = {}
        self._sync_task: asyncio.Task[None] | None = None
        self._plugin_config: UniFiPluginConfig = UniFiPluginConfig(**config)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        """Initialize: load controller configs from DB and create API clients."""
        def _load():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(UniFiController).where(
                            UniFiController.enabled.is_(True)
                        )
                    ).scalars().all()
                )
            finally:
                session.close()

        controllers = await asyncio.to_thread(_load)

        for ctrl in controllers:
            api_key = ""
            if ctrl.encrypted_api_key:
                try:
                    from app.core.config import get_settings
                    from app.core.security import CredentialCipher
                    cipher = CredentialCipher(
                        get_settings().missioncontrol_secret_key
                    )
                    api_key = cipher.decrypt(ctrl.encrypted_api_key)
                except Exception:
                    api_key = ""

            client = UniFiApiClient(
                url=ctrl.url,
                api_key=api_key,
                verify_ssl=ctrl.verify_ssl,
                timeout=ctrl.timeout,
                controller_type=ctrl.controller_type,
            )
            self._clients[ctrl.id] = client

        logger.info(
            "UniFi plugin setup: %d controller(s) configured",
            len(self._clients),
        )

    async def start(self) -> None:
        """Start background sync task."""
        if self._plugin_config.auto_sync_enabled and self._clients:
            self._sync_task = asyncio.create_task(self._background_sync())
            logger.info(
                "UniFi background sync started (interval=%ds)",
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
        logger.info("UniFi plugin stopped")

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def _background_sync(self) -> None:
        """Periodically sync data from all enabled controllers."""
        while True:
            try:
                await self._run_sync_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("UniFi sync cycle failed")
            await asyncio.sleep(self._plugin_config.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Run one sync cycle for all controllers."""
        def _load_controllers():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(UniFiController).where(
                            UniFiController.enabled.is_(True)
                        )
                    ).scalars().all()
                )
            finally:
                session.close()

        controllers = await asyncio.to_thread(_load_controllers)

        for ctrl in controllers:
            client = self._clients.get(ctrl.id)
            if not client:
                continue
            try:
                await self._sync_controller(client, ctrl.id)
                logger.debug("Sync completed for controller %s", ctrl.name)

                await event_bus.publish(Event(
                    type=EventType.PLUGIN_HEALTH_CHANGED,
                    data={"plugin": "unifi", "controller_id": ctrl.id, "status": "synced"},
                    source="plugin.unifi",
                ))

            except Exception as exc:
                logger.warning(
                    "Sync failed for controller %s: %s", ctrl.name, exc,
                )
                await self._mark_controller_error(ctrl.id, str(exc)[:500])

                await event_bus.publish(Event(
                    type=EventType.PLUGIN_HEALTH_CHANGED,
                    data={
                        "plugin": "unifi",
                        "controller_id": ctrl.id,
                        "status": "sync_failed",
                        "error": str(exc)[:200],
                    },
                    source="plugin.unifi",
                ))

    async def _sync_controller(self, client: UniFiApiClient, controller_id: int) -> None:
        """Sync all data for a single controller."""
        ctrl_sync = ControllerSync()
        site_sync = SiteSync()
        dev_sync = DeviceSync()
        client_sync = ClientSync()
        alert_sync = AlertSync()
        net_sync = NetworkSync()

        def _do_sync():
            session = SessionLocal()
            try:
                ctrl_sync.sync(session, client, controller_id)
                site_sync.sync(session, client, controller_id)
                dev_sync.sync(session, client, controller_id)
                client_sync.sync(session, client, controller_id)
                alert_sync.sync(session, client, controller_id)
                net_sync.sync(session, client, controller_id)
            finally:
                session.close()

        await asyncio.to_thread(_do_sync)

    @staticmethod
    async def _mark_controller_error(controller_id: int, error_msg: str) -> None:
        """Write error state for a controller in a background thread."""

        def _write():
            session = SessionLocal()
            try:
                ctrl = session.get(UniFiController, controller_id)
                if ctrl:
                    ctrl.status = "error"
                    ctrl.last_error = error_msg
                    ctrl.last_sync_at = datetime.now(UTC)
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
                "id": "unifi-summary",
                "title": "UniFi Network Overview",
                "component": "UniFiSummaryWidget",
                "size": "large",
                "refresh_interval": 120,
            },
            {
                "id": "unifi-devices-by-status",
                "title": "Devices by Status",
                "component": "UniFiDevicesByStatusWidget",
                "size": "medium",
                "refresh_interval": 60,
            },
            {
                "id": "unifi-devices-by-type",
                "title": "Devices by Type",
                "component": "UniFiDevicesByTypeWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "unifi-access-points",
                "title": "Access Points",
                "component": "UniFiAccessPointsWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "unifi-switches",
                "title": "Switches",
                "component": "UniFiSwitchesWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "unifi-gateways",
                "title": "Gateways",
                "component": "UniFiGatewaysWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "unifi-clients",
                "title": "Connected Clients",
                "component": "UniFiClientsWidget",
                "size": "large",
                "refresh_interval": 60,
            },
            {
                "id": "unifi-alerts",
                "title": "Recent Alerts",
                "component": "UniFiAlertsWidget",
                "size": "medium",
                "refresh_interval": 60,
            },
            {
                "id": "unifi-wireless",
                "title": "Wireless Networks",
                "component": "UniFiWirelessWidget",
                "size": "small",
                "refresh_interval": 300,
            },
            {
                "id": "unifi-controllers",
                "title": "Controllers",
                "component": "UniFiControllersWidget",
                "size": "small",
                "refresh_interval": 120,
            },
            {
                "id": "unifi-sites",
                "title": "Sites",
                "component": "UniFiSitesWidget",
                "size": "small",
                "refresh_interval": 300,
            },
            {
                "id": "unifi-topology",
                "title": "Network Topology",
                "component": "UniFiTopologyWidget",
                "size": "large",
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
        if widget_id == "unifi-summary":
            return cache_manager.get_summary(session)
        if widget_id == "unifi-devices-by-status":
            return {"devices_by_status": cache_manager.get_devices_by_status(session)}
        if widget_id == "unifi-devices-by-type":
            return {"devices_by_type": cache_manager.get_devices_by_type(session)}
        if widget_id == "unifi-access-points":
            return {"access_points": cache_manager.get_access_points(session)}
        if widget_id == "unifi-switches":
            return {"switches": cache_manager.get_switches(session)}
        if widget_id == "unifi-gateways":
            return {"gateways": cache_manager.get_gateways(session)}
        if widget_id == "unifi-clients":
            clients = cache_manager.get_clients(session)
            return {"clients": clients[:100], "total_count": len(clients)}
        if widget_id == "unifi-alerts":
            alerts = cache_manager.get_alerts(session)
            return {"alerts": alerts[:50], "total_count": len(alerts)}
        if widget_id == "unifi-wireless":
            return {"wireless_networks": cache_manager.get_wireless(session)}
        if widget_id == "unifi-controllers":
            return {"controllers": cache_manager.get_controllers(session)}
        if widget_id == "unifi-sites":
            return {"sites": cache_manager.get_sites(session)}
        if widget_id == "unifi-topology":
            summary = cache_manager.get_summary(session)
            devices = cache_manager.get_devices(session)
            return {"summary": summary, "devices": devices}
        return {}

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "unifi-dashboard",
                "label": "UniFi Dashboard",
                "icon": "wifi",
                "path": "/plugins/unifi",
                "group": "Networking",
                "order": 10,
            },
            {
                "id": "unifi-devices",
                "label": "Devices",
                "icon": "router",
                "path": "/plugins/unifi/devices",
                "group": "Networking",
                "order": 20,
            },
            {
                "id": "unifi-clients",
                "label": "Clients",
                "icon": "users",
                "path": "/plugins/unifi/clients",
                "group": "Networking",
                "order": 30,
            },
            {
                "id": "unifi-alerts",
                "label": "Alerts",
                "icon": "bell",
                "path": "/plugins/unifi/alerts",
                "group": "Networking",
                "order": 40,
            },
            {
                "id": "unifi-wireless",
                "label": "Wireless",
                "icon": "radio",
                "path": "/plugins/unifi/wireless",
                "group": "Networking",
                "order": 50,
            },
            {
                "id": "unifi-controllers",
                "label": "Controllers",
                "icon": "server",
                "path": "/plugins/unifi/controllers",
                "group": "Networking",
                "order": 60,
            },
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {
                "path": "/api/v1/plugins/unifi",
                "router": router,
                "summary": "UniFi plugin API",
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
                "max_clients": {
                    "type": "integer",
                    "title": "Max clients to cache",
                    "minimum": 100,
                    "maximum": 10000,
                    "default": 2000,
                },
                "max_devices": {
                    "type": "integer",
                    "title": "Max devices to cache",
                    "minimum": 10,
                    "maximum": 2000,
                    "default": 500,
                },
                "max_alerts": {
                    "type": "integer",
                    "title": "Max alerts to cache",
                    "minimum": 50,
                    "maximum": 5000,
                    "default": 500,
                },
                "alert_retention_days": {
                    "type": "integer",
                    "title": "Alert retention (days)",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                },
                "client_retention_days": {
                    "type": "integer",
                    "title": "Client retention (days)",
                    "minimum": 1,
                    "maximum": 90,
                    "default": 7,
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
                "temperature_warning_c": {
                    "type": "number",
                    "title": "Temperature warning (C)",
                    "minimum": 40,
                    "maximum": 85,
                    "default": 60,
                },
                "temperature_critical_c": {
                    "type": "number",
                    "title": "Temperature critical (C)",
                    "minimum": 60,
                    "maximum": 100,
                    "default": 75,
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self._plugin_config = UniFiPluginConfig(**settings)
        self.config.update(settings)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        if not self._clients:
            return {"status": "warning", "message": "No controllers configured"}

        healthy = 0
        errors: list[str] = []
        for _ctrl_id, client in self._clients.items():
            try:
                result = await client.test_connection()
                if result.get("connected"):
                    healthy += 1
                else:
                    errors.append(result.get("error", "unreachable"))
            except Exception as exc:
                errors.append(str(exc)[:200])

        total = len(self._clients)
        if healthy == total:
            return {"status": "ok", "controllers": total, "healthy": healthy}
        if healthy > 0:
            return {
                "status": "degraded",
                "controllers": total,
                "healthy": healthy,
                "errors": errors,
            }
        return {
            "status": "error",
            "controllers": total,
            "healthy": 0,
            "errors": errors,
        }
