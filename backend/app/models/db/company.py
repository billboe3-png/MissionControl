"""
Mission Control Company ORM Model

Sprint 2.9 - Multi-Tenant & Multi-Site Platform.

Companies (tenants) are the top-level organizational unit. Every site,
user, agent, integration, and resource belongs to a company. Company
isolation is absolute — nothing belonging to Company A is ever visible
to Company B.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Company(Base):
    """
    A company (tenant) in the multi-tenant platform.

    Each company has its own sites, users, agents, integrations,
    dashboards, AI, and automation. Global administrators can view
    and manage all companies.
    """

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # Status & Licensing                                                  #
    # ------------------------------------------------------------------ #

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    license_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    max_sites: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    max_agents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )

    max_users: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
    )

    # ------------------------------------------------------------------ #
    # Contact                                                             #
    # ------------------------------------------------------------------ #

    primary_contact: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    contact_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Configuration                                                       #
    # ------------------------------------------------------------------ #

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    theme: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Notes                                                               #
    # ------------------------------------------------------------------ #

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Flags                                                               #
    # ------------------------------------------------------------------ #

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_global: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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
