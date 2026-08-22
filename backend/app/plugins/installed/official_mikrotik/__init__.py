"""
MikroTik Plugin Implementation
"""
import asyncio
import contextlib
import logging
from typing import Any

from sqlalchemy import select

from app.db.database import SessionLocal
from app.plugins.installed.official_mikrotik.cache import cache_manager
from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.routes import router
from app.plugins.installed.official_mikrotik.ssh_client import MikroTikSSHClient
from app.plugins.server import ServerPluginSDK

logger = logging.getLogger("plugin.mikrotik")


class MikroTikPlugin(ServerPluginSDK):
    """MikroTik RouterOS monitoring integration plugin."""

    def __init__(self, manifest: dict[str, Any], config: dict[str, Any]) -> None:
        super().__init__(manifest, config)
        self._sync_task = None

    async def setup(self) -> None:
        logger.info("MikroTik plugin setup")

    async def start(self) -> None:
        self._sync_task = asyncio.create_task(self._background_sync())
        logger.info("MikroTik background sync started")

    async def stop(self) -> None:
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task
        logger.info("MikroTik plugin stopped")

    async def _background_sync(self) -> None:
        while True:
            try:
                session = SessionLocal()
                try:
                    servers = list(
                        session.execute(
                            select(MikroTikServer).where(MikroTikServer.enabled.is_(True))
                        ).scalars().all()
                    )
                finally:
                    session.close()

                for server in servers:
                    try:
                        client = MikroTikSSHClient(
                            host=server.host,
                            username=server.username,
                            password=server.password_encrypted or "",
                            port=server.ssh_port,
                        )
                        interfaces_raw = await client.execute("/interface print detail")
                        interfaces = MikroTikSSHClient._parse_key_value_output(interfaces_raw)

                        firewall_raw = await client.execute("/ip firewall filter print detail")
                        rules = MikroTikSSHClient._parse_key_value_output(firewall_raw)

                        dhcp_raw = await client.execute("/ip dhcp-server lease print detail")
                        leases = MikroTikSSHClient._parse_key_value_output(dhcp_raw)

                        resource_raw = await client.execute("/system resource print")
                        resource = MikroTikSSHClient._parse_key_value_output(resource_raw)
                        info = resource[0] if resource else {}

                        session = SessionLocal()
                        try:
                            cache_manager.replace_interfaces(session, server.id, interfaces)
                            cache_manager.replace_firewall_rules(session, server.id, rules)
                            cache_manager.replace_dhcp_leases(session, server.id, leases)
                            server.version = info.get("version")
                            server.board_name = info.get("board-name")
                            server.cpu_load = info.get("cpu-load")
                            server.uptime = info.get("uptime")
                            cache_manager.mark_sync(session, server.id, "ok")
                            session.flush()
                        finally:
                            session.close()
                    except Exception as exc:
                        logger.warning("Sync failed for MikroTik %s: %s", server.host, exc)
                        try:
                            session = SessionLocal()
                            cache_manager.mark_sync(session, server.id, "error", str(exc))
                            session.close()
                        except Exception:
                            logger.warning("Failed to mark sync error for server %s", server.id)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("MikroTik sync cycle failed")
            await asyncio.sleep(300)

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

    def get_routes(self) -> list[dict[str, Any]]:
        return [{"path": "/api/v1/plugins/mikrotik", "router": router}]
