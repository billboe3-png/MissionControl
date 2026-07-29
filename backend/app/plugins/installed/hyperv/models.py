"""
Hyper-V Plugin SQLAlchemy Models

Tables for caching Hyper-V data locally:
- hyperv_hosts: registered Hyper-V host connections (from IntegrationProfile)
- hyperv_vms: cached VM inventory
- hyperv_networks: cached virtual switch data
- hyperv_volumes: cached virtual hard disk data
- hyperv_checkpoints: cached checkpoint data
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


class HyperVHost(Base):
    """Registered Hyper-V host connection (mirrors IntegrationProfile)."""

    __tablename__ = "hyperv_hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    integration_profile_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True,
        comment="FK to integration_profiles.id (nullable for agent-relayed hosts)",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    hostname: Mapped[str] = mapped_column(String(500), nullable=False)
    transport: Mapped[str] = mapped_column(
        String(20), nullable=False, default="winrm",
        comment="winrm or ssh",
    )
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=5985)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class HyperVVM(Base):
    """Cached Hyper-V virtual machine inventory."""

    __tablename__ = "hyperv_vms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hyperv_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    vm_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    cpu_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_assigned_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_startup_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_demand_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uptime_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    host_server: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_os: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creation_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_checkpoint: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    integration_services_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    cpu_usage_percent: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    disk_read_mbps: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    disk_write_mbps: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    network_receive_mbps: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    network_send_mbps: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class HyperVNetwork(Base):
    """Cached Hyper-V virtual switch data."""

    __tablename__ = "hyperv_networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hyperv_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    switch_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    switch_type: Mapped[str] = mapped_column(String(20), nullable=False, default="external")
    allow_management_os: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="operational")
    connected_vms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    net_adapter: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class HyperVVolume(Base):
    """Cached Hyper-V virtual hard disk data."""

    __tablename__ = "hyperv_volumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hyperv_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    disk_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="vhdx")
    vm_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class HyperVCheckpoint(Base):
    """Cached Hyper-V checkpoint data."""

    __tablename__ = "hyperv_checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hyperv_hosts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    checkpoint_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vm_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vm_name: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    checkpoint_type: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    creation_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_checkpoint_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
