"""
MikroTik Sync Module
"""
import asyncio
import logging

from sqlalchemy import select

from app.db.database import SessionLocal
from app.plugins.installed.official_mikrotik.cache import cache_manager
from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.ssh_client import MikroTikSSHClient

logger = logging.getLogger("plugin.mikrotik.sync")


async def sync_all() -> None:
    """Sync all enabled MikroTik servers."""
    def _load():
        session = SessionLocal()
        try:
            return list(
                session.execute(
                    select(MikroTikServer).where(MikroTikServer.enabled.is_(True))
                ).scalars().all()
            )
        finally:
            session.close()

    servers = await asyncio.to_thread(_load)
    for server in servers:
        try:
            await _sync_server(server)
            session = SessionLocal()
            cache_manager.mark_sync(session, server.id, "ok")
            session.close()
        except Exception as exc:
            logger.warning("Sync failed for MikroTik %s: %s", server.host, exc)
            try:
                session = SessionLocal()
                cache_manager.mark_sync(session, server.id, "error", str(exc))
                session.close()
            except Exception as exc:
                logger.warning("Mark sync error state failed: %s", exc)


async def _sync_server(server: MikroTikServer) -> None:
    """Sync data from a single MikroTik server."""
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
        session.flush()
    finally:
        session.close()
