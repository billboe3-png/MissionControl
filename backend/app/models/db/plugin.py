"""
Mission Control Plugin ORM Model

Sprint 3.1 - Distributed Plugin Architecture.

Stores metadata for installed plugins (server, agent, and hybrid).
Each plugin has a unique slug, manifest-derived metadata, and
lifecycle state managed by the PluginRegistry service.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Plugin(Base):
    """
    Installed plugin metadata.

    A plugin represents a registered extension that can provide
    dashboard widgets, REST APIs, pages, agent commands, or
    hybrid server+agent functionality.
    """

    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Identity                                                            #
    # ------------------------------------------------------------------ #

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Classification                                                      #
    # ------------------------------------------------------------------ #

    execution_target: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # "server" | "agent" | "hybrid"

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )  # "monitoring", "backup", "identity", "automation", etc.

    # ------------------------------------------------------------------ #
    # State                                                               #
    # ------------------------------------------------------------------ #

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="registered",
        index=True,
    )  # "registered" | "initializing" | "running" | "stopped" | "error"

    # ------------------------------------------------------------------ #
    # Configuration                                                       #
    # ------------------------------------------------------------------ #

    config_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # JSON-serialized plugin-specific configuration

    # ------------------------------------------------------------------ #
    # Capabilities (declared by manifest)                                 #
    # ------------------------------------------------------------------ #

    capabilities_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # JSON-serialized list of capabilities

    # ------------------------------------------------------------------ #
    # Compatibility                                                       #
    # ------------------------------------------------------------------ #

    min_core_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # Minimum Mission Control version required

    # ------------------------------------------------------------------ #
    # Permissions                                                         #
    # ------------------------------------------------------------------ #

    permissions_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # JSON-serialized list of required permissions

    # ------------------------------------------------------------------ #
    # Dependencies                                                        #
    # ------------------------------------------------------------------ #

    dependencies_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # JSON-serialized list of plugin slugs this depends on

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
