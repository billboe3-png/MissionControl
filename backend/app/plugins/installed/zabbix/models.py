"""
Zabbix Plugin SQLAlchemy Models

Tables for caching Zabbix data locally:
- zabbix_servers: registered Zabbix server connections
- zabbix_hosts: cached host inventory
- zabbix_problems: cached problem/trigger data
- zabbix_events: cached event history
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ZabbixServer(Base):
    """Registered Zabbix server connection."""

    __tablename__ = "zabbix_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    encrypted_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class ZabbixHost(Base):
    """Cached Zabbix host inventory."""

    __tablename__ = "zabbix_hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("zabbix_servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zabbix_hostid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="enabled")
    available: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    interface_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    groups_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    templates_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class ZabbixProblem(Base):
    """Cached Zabbix problems (active triggers)."""

    __tablename__ = "zabbix_problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("zabbix_servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zabbix_eventid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(1000), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="not_classified")
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    host: Mapped[str | None] = mapped_column(String(200), nullable=True)
    zabbix_hostid: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class ZabbixEvent(Base):
    """Cached Zabbix event history."""

    __tablename__ = "zabbix_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("zabbix_servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zabbix_eventid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(1000), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="not_classified")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OK")
    host: Mapped[str | None] = mapped_column(String(200), nullable=True)
    zabbix_hostid: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
