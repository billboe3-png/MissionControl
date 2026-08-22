"""
MikroTik Cache Manager
"""
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.plugins.installed.official_mikrotik.models import (
    MikroTikDhcpLease,
    MikroTikFirewallRule,
    MikroTikInterface,
    MikroTikServer,
)

logger = logging.getLogger("plugin.mikrotik.cache")


class MikroTikCacheManager:
    """Cache manager for MikroTik plugin data."""

    def get_servers(self, db: Session) -> list[dict[str, Any]]:
        """List all MikroTik servers."""
        rows = db.execute(select(MikroTikServer)).scalars().all()
        return [self._server_to_dict(r) for r in rows]

    def get_server(self, db: Session, server_id: int) -> dict[str, Any] | None:
        """Get a single server by ID."""
        row = db.get(MikroTikServer, server_id)
        return self._server_to_dict(row) if row else None

    def upsert_server(self, db: Session, data: dict[str, Any]) -> MikroTikServer:
        """Create or update a server row."""
        server = db.get(MikroTikServer, data.get("id")) if data.get("id") else None
        if server is None:
            server = MikroTikServer()
            db.add(server)

        for key, value in data.items():
            if key in {"id", "created_at", "updated_at"}:
                continue
            if hasattr(server, key):
                setattr(server, key, value)

        db.flush()
        return server

    def delete_server(self, db: Session, server_id: int) -> bool:
        """Delete a server and its cached data."""
        server = db.get(MikroTikServer, server_id)
        if server is None:
            return False

        db.execute(delete(MikroTikInterface).where(MikroTikInterface.server_id == server_id))
        db.execute(delete(MikroTikFirewallRule).where(MikroTikFirewallRule.server_id == server_id))
        db.execute(delete(MikroTikDhcpLease).where(MikroTikDhcpLease.server_id == server_id))
        db.delete(server)
        db.flush()
        return True

    def mark_sync(self, db: Session, server_id: int, status: str, error: str | None = None) -> None:
        """Mark last sync time and status."""
        server = db.get(MikroTikServer, server_id)
        if server is None:
            return
        server.last_sync_at = datetime.now(UTC)
        server.status = status
        if error:
            server.last_error = error[:500]
        db.flush()

    def get_interfaces(self, db: Session, server_id: int) -> list[dict[str, Any]]:
        """Get cached interfaces for a server."""
        rows = db.execute(
            select(MikroTikInterface).where(MikroTikInterface.server_id == server_id)
        ).scalars().all()
        return [
            {
                "name": r.name,
                "type": r.type,
                "status": r.status,
                "link_status": r.link_status,
                "rx_bytes": r.rx_byte_count,
                "tx_bytes": r.tx_byte_count,
                "rx_packets": r.rx_packet_count,
                "tx_packets": r.tx_packet_count,
                "mac": r.mac_address,
                "mtu": r.actual_mtu,
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
            }
            for r in rows
        ]

    def get_firewall_rules(self, db: Session, server_id: int) -> list[dict[str, Any]]:
        """Get cached firewall rules for a server."""
        rows = db.execute(
            select(MikroTikFirewallRule).where(MikroTikFirewallRule.server_id == server_id)
        ).scalars().all()
        return [
            {
                "chain": r.chain,
                "action": r.action,
                "comment": r.comment,
                "disabled": r.disabled,
                "bytes": r.bytes_count,
                "packets": r.packet_count,
            }
            for r in rows
        ]

    def get_dhcp_leases(self, db: Session, server_id: int) -> list[dict[str, Any]]:
        """Get cached DHCP leases for a server."""
        rows = db.execute(
            select(MikroTikDhcpLease).where(MikroTikDhcpLease.server_id == server_id)
        ).scalars().all()
        return [
            {
                "address": r.address,
                "mac": r.mac_address,
                "host_name": r.host_name,
                "status": r.status,
                "expires": r.expires_after,
            }
            for r in rows
        ]

    def replace_interfaces(self, db: Session, server_id: int, interfaces: list[dict[str, Any]]) -> None:
        """Replace cached interfaces."""
        db.execute(delete(MikroTikInterface).where(MikroTikInterface.server_id == server_id))
        for item in interfaces:
            db.add(
                MikroTikInterface(
                    server_id=server_id,
                    name=item.get("name", ""),
                    type=item.get("type"),
                    status=item.get("status"),
                    link_status=item.get("link_status"),
                    rx_byte_count=int(item.get("rx_bytes", 0) or 0),
                    tx_byte_count=int(item.get("tx_bytes", 0) or 0),
                    rx_packet_count=int(item.get("rx_packets", 0) or 0),
                    tx_packet_count=int(item.get("tx_packets", 0) or 0),
                    mac_address=item.get("mac"),
                    actual_mtu=int(item["mtu"]) if item.get("mtu") else None,
                    last_seen=datetime.now(UTC),
                )
            )
        db.flush()

    def replace_firewall_rules(self, db: Session, server_id: int, rules: list[dict[str, Any]]) -> None:
        """Replace cached firewall rules."""
        db.execute(delete(MikroTikFirewallRule).where(MikroTikFirewallRule.server_id == server_id))
        for item in rules:
            db.add(
                MikroTikFirewallRule(
                    server_id=server_id,
                    chain=item.get("chain", ""),
                    action=item.get("action"),
                    comment=item.get("comment"),
                    disabled=bool(item.get("disabled", False)),
                    bytes_count=int(item.get("bytes", 0) or 0),
                    packet_count=int(item.get("packets", 0) or 0),
                )
            )
        db.flush()

    def replace_dhcp_leases(self, db: Session, server_id: int, leases: list[dict[str, Any]]) -> None:
        """Replace cached DHCP leases."""
        db.execute(delete(MikroTikDhcpLease).where(MikroTikDhcpLease.server_id == server_id))
        for item in leases:
            db.add(
                MikroTikDhcpLease(
                    server_id=server_id,
                    address=item.get("address"),
                    mac_address=item.get("mac", ""),
                    host_name=item.get("host_name"),
                    client_id=item.get("client_id"),
                    status=item.get("status"),
                    expires_after=item.get("expires"),
                )
            )
        db.flush()

    @staticmethod
    def _server_to_dict(server: MikroTikServer | None) -> dict[str, Any] | None:
        if server is None:
            return None
        return {
            "id": server.id,
            "name": server.name,
            "host": server.host,
            "ssh_port": server.ssh_port,
            "telnet_enabled": server.telnet_enabled,
            "telnet_port": server.telnet_port,
            "username": server.username,
            "api_enabled": server.api_enabled,
            "api_port": server.api_port,
            "enabled": server.enabled,
            "status": server.status,
            "last_error": server.last_error,
            "version": server.version,
            "board_name": server.board_name,
            "cpu_load": server.cpu_load,
            "memory_usage_pct": server.memory_usage_pct,
            "uptime": server.uptime,
            "last_sync_at": server.last_sync_at.isoformat() if server.last_sync_at else None,
            "created_at": server.created_at.isoformat() if server.created_at else None,
        }


cache_manager = MikroTikCacheManager()
