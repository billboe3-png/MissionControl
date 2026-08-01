"""
Mission Control Agent ORM Model

Sprint 2.7 - Mission Control Agent.

Stores registered agent instances that communicate with Mission Control
via outbound HTTPS. The agent pushes heartbeats, inventory, and command
results; Mission Control dispatches commands and file transfers.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Agent(Base):
    """
    A registered Mission Control Agent instance.

    Agents connect outbound-only via HTTPS, so no inbound firewall
    ports are required. Each agent has a unique API key and reports
    its status, version, and inventory periodically.
    """

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    site_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    hostname: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    api_key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="offline",
        index=True,
    )

    # ------------------------------------------------------------------ #
    # System Info                                                         #
    # ------------------------------------------------------------------ #

    operating_system: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    os_version: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    agent_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Inventory (JSON-serialized)                                         #
    # ------------------------------------------------------------------ #

    inventory_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Heartbeat                                                           #
    # ------------------------------------------------------------------ #

    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    heartbeat_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    # ------------------------------------------------------------------ #
    # Configuration                                                       #
    # ------------------------------------------------------------------ #

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    tags: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    health: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unknown",
    )

    cpu_percent: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    memory_percent: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    disk_percent: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Plugin Support                                                      #
    # ------------------------------------------------------------------ #

    active_plugins: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    enabled_plugins: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated plugins enabled by the user/server.",
    )

    # ------------------------------------------------------------------ #
    # Timestamps                                                          #
    # ------------------------------------------------------------------ #

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
