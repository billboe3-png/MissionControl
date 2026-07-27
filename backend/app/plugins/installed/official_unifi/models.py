"""
UniFi Plugin SQLAlchemy Models

Tables for caching UniFi data locally:
- unifi_controllers: registered controller connections
- unifi_sites: cached site inventory
- unifi_devices: cached device inventory
- unifi_clients: cached client inventory
- unifi_alerts: cached alert history
- unifi_wireless_networks: cached wireless network config
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UniFiController(Base):
    """Registered UniFi controller or Site Manager connection."""

    __tablename__ = "unifi_controllers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    controller_type: Mapped[str] = mapped_column(String(20), nullable=False, default="cloud")
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    organization_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UniFiSite(Base):
    """Cached UniFi site information."""

    __tablename__ = "unifi_sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    controller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("unifi_controllers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    unifi_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    isp_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    wan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    num_devices: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_clients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UniFiDevice(Base):
    """Cached UniFi device inventory."""

    __tablename__ = "unifi_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    controller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("unifi_controllers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    site_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unifi_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    serial: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adoption_state: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="offline")
    uptime_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpu_utilization: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_utilization: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    device_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UniFiClient(Base):
    """Cached UniFi client inventory."""

    __tablename__ = "unifi_clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    controller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("unifi_controllers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    site_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unifi_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hostname: Mapped[str | None] = mapped_column(String(300), nullable=True)
    mac_address: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vlan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    connected_ap_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    connected_switch_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rx_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tx_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_wired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class UniFiAlert(Base):
    """Cached UniFi alert history."""

    __tablename__ = "unifi_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    controller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("unifi_controllers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    site_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unifi_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class UniFiWirelessNetwork(Base):
    """Cached UniFi wireless network configuration."""

    __tablename__ = "unifi_wireless_networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    controller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("unifi_controllers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    site_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unifi_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ssid: Mapped[str] = mapped_column(String(200), nullable=False)
    security: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    vlan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
