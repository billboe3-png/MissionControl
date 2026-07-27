"""
Zabbix Monitoring Plugin

Community plugin for Zabbix monitoring integration.
Provides inventory sync, problem tracking, event aggregation,
dashboard widgets, and plugin-scoped REST API.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.events import Event, EventType, event_bus
from app.plugins.installed.zabbix.api import ZabbixApiClient
from app.plugins.installed.zabbix.config import ZabbixPluginConfig
from app.plugins.installed.zabbix.models import (
    ZabbixHost,
    ZabbixProblem,
    ZabbixServer,
)
from app.plugins.installed.zabbix.routes import router
from app.plugins.installed.zabbix.sync import EventSync, InventorySync, ProblemSync
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.zabbix")


def _db_session():
    """Return a new synchronous DB session (context manager)."""
    return SessionLocal()


class ZabbixPlugin(ServerPluginSDK):
    """Zabbix monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._clients: dict[int, ZabbixApiClient] = {}
        self._sync_task: asyncio.Task[None] | None = None
        self._plugin_config: ZabbixPluginConfig = ZabbixPluginConfig(**config)

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
                        select(ZabbixServer).where(ZabbixServer.enabled.is_(True))
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
                    cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
                    password = cipher.decrypt(server.encrypted_password)
                except Exception:
                    password = ""
            else:
                password = ""

            client = ZabbixApiClient(
                url=server.url,
                username=server.username,
                password=password,
                verify_ssl=server.verify_ssl,
                timeout=server.timeout,
                retries=server.retries,
            )
            self._clients[server.id] = client

        logger.info(
            "Zabbix plugin setup: %d server(s) configured", len(self._clients)
        )

    async def start(self) -> None:
        """Start background sync task."""
        if self._plugin_config.auto_sync_enabled and self._clients:
            self._sync_task = asyncio.create_task(self._background_sync())
            logger.info(
                "Zabbix background sync started (interval=%ds)",
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

        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        logger.info("Zabbix plugin stopped")

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def _background_sync(self) -> None:
        """Periodically sync data from all enabled Zabbix servers."""
        while True:
            try:
                await self._run_sync_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Zabbix sync cycle failed")
            await asyncio.sleep(self._plugin_config.sync_interval_seconds)

    async def _run_sync_cycle(self) -> None:
        """Run one sync cycle for all servers."""
        def _load_servers():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(ZabbixServer).where(ZabbixServer.enabled.is_(True))
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
                await self._sync_server(client, server)
                logger.debug("Sync completed for server %s", server.name)
            except Exception as exc:
                logger.warning("Sync failed for server %s: %s", server.name, exc)
                await self._mark_server_error(server.id, str(exc)[:500])

        # Publish summary event
        await event_bus.publish(Event(
            type=EventType.PLUGIN_HEALTH_CHANGED,
            data={"plugin": "zabbix", "status": "synced"},
            source="plugin.zabbix",
        ))

    async def _sync_server(self, client: "ZabbixApiClient", server: "ZabbixServer") -> None:
        """Sync inventory, problems, and events for a single server."""
        await client.ensure_auth()
        inv_sync = InventorySync()
        prob_sync = ProblemSync()
        evt_sync = EventSync()
        server_id = server.id
        max_problems = self._plugin_config.max_problems_per_host * 10

        def _do_sync():
            session = SessionLocal()
            try:
                inv_sync.sync(session, client, server_id)
                prob_sync.sync(session, client, server_id, limit=max_problems)
                evt_sync.sync(session, client, server_id, limit=100)
                server_row = session.get(ZabbixServer, server_id)
                if server_row:
                    server_row.last_sync_at = datetime.now(UTC)
                    server_row.status = "healthy"
                    server_row.last_error = None
                session.commit()
            finally:
                session.close()

        await asyncio.to_thread(_do_sync)

    @staticmethod
    async def _mark_server_error(server_id: int, error_msg: str) -> None:
        """Write error state for a server in a background thread."""

        def _write():
            session = SessionLocal()
            try:
                server_row = session.get(ZabbixServer, server_id)
                if server_row:
                    server_row.status = "error"
                    server_row.last_error = error_msg
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
                "id": "zabbix-summary",
                "title": "Zabbix Overview",
                "component": "ZabbixSummaryWidget",
                "size": "large",
                "refresh_interval": 60,
            },
            {
                "id": "zabbix-problems",
                "title": "Active Problems",
                "component": "ZabbixProblemsWidget",
                "size": "medium",
                "refresh_interval": 30,
            },
        ]

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        if widget_id == "zabbix-summary":
            return await self._get_summary_widget()
        if widget_id == "zabbix-problems":
            return await self._get_problems_widget()
        return {}

    async def _get_summary_widget(self) -> dict[str, Any]:
        def _query():
            session = SessionLocal()
            try:
                host_count = (session.execute(
                    select(func.count(ZabbixHost.id))
                )).scalar() or 0
                available_count = (session.execute(
                    select(func.count(ZabbixHost.id)).where(ZabbixHost.available == "available")
                )).scalar() or 0
                problem_count = (session.execute(
                    select(func.count(ZabbixProblem.id)).where(ZabbixProblem.resolved_at.is_(None))
                )).scalar() or 0
                return host_count, available_count, problem_count
            finally:
                session.close()

        host_count, available_count, problem_count = await asyncio.to_thread(_query)
        return {
            "host_count": host_count,
            "available_count": available_count,
            "unavailable_count": host_count - available_count,
            "problem_count": problem_count,
            "server_count": len(self._clients),
        }

    async def _get_problems_widget(self) -> dict[str, Any]:
        def _query():
            session = SessionLocal()
            try:
                return list(
                    session.execute(
                        select(ZabbixProblem)
                        .where(ZabbixProblem.resolved_at.is_(None))
                        .order_by(ZabbixProblem.id.desc())
                        .limit(10)
                    ).scalars().all()
                )
            finally:
                session.close()

        problems = await asyncio.to_thread(_query)
        return {
            "problems": [
                {
                    "name": p.name,
                    "severity": p.severity,
                    "host": p.host,
                    "acknowledged": p.acknowledged,
                    "timestamp": p.timestamp,
                }
                for p in problems
            ],
            "total_count": len(problems),
        }

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "zabbix-overview",
                "label": "Zabbix Overview",
                "icon": "activity",
                "path": "/plugins/zabbix",
                "group": "Monitoring",
                "order": 10,
            },
            {
                "id": "zabbix-hosts",
                "label": "Hosts",
                "icon": "server",
                "path": "/plugins/zabbix/hosts",
                "group": "Monitoring",
                "order": 20,
            },
            {
                "id": "zabbix-problems",
                "label": "Problems",
                "icon": "alert-triangle",
                "path": "/plugins/zabbix/problems",
                "group": "Monitoring",
                "order": 30,
            },
        ]

    # ------------------------------------------------------------------ #
    # REST API routes                                                     #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        return [
            {
                "path": "/api/v1/plugins/zabbix",
                "router": router,
                "summary": "Zabbix plugin API",
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
                "max_problems_per_host": {
                    "type": "integer",
                    "title": "Max problems per host",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 50,
                },
                "event_retention_days": {
                    "type": "integer",
                    "title": "Event retention (days)",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30,
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self._plugin_config.model_dump()

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self._plugin_config = ZabbixPluginConfig(**settings)
        self.config.update(settings)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        if not self._clients:
            return {"status": "warning", "message": "No servers configured"}

        healthy = 0
        for _server_id, client in self._clients.items():
            try:
                result = await client.test_connection()
                if result.get("connected"):
                    healthy += 1
            except Exception:
                pass

        total = len(self._clients)
        if healthy == total:
            return {"status": "ok", "servers": total, "healthy": healthy}
        if healthy > 0:
            return {"status": "degraded", "servers": total, "healthy": healthy}
        return {"status": "error", "servers": total, "healthy": 0}
