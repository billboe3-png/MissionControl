"""
MikroTik Plugin SQLAlchemy Models
"""
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MikroTikServer(Base):
    """Registered MikroTik RouterOS device."""

    __tablename__ = "mikrotik_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    host: Mapped[str] = mapped_column(String(500), nullable=False)
    ssh_port: Mapped[int] = mapped_column(Integer, nullable=False, default=22)
    telnet_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    telnet_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relay_agent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    remote_target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    allow_insecure_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    board_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cpu_load: Mapped[str | None] = mapped_column(String(20), nullable=True)
    memory_usage_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uptime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class MikroTikCommandLog(Base):
    """Audit log of commands executed against a MikroTik server."""

    __tablename__ = "mikrotik_command_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_type: Mapped[str] = mapped_column(String(20), nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    executed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )


class MikroTikInterface(Base):
    """Cached interface status."""

    __tablename__ = "mikrotik_interfaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    link_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rx_byte_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tx_byte_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    rx_packet_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tx_packet_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mac_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actual_mtu: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class MikroTikFirewallRule(Base):
    """Cached firewall filter rule."""

    __tablename__ = "mikrotik_firewall_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(300), nullable=True)
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bytes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    packet_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class MikroTikDhcpLease(Base):
    """Cached DHCP lease."""

    __tablename__ = "mikrotik_dhcp_leases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    host_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    expires_after: Mapped[str | None] = mapped_column(String(100), nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
