"""
Mission Control Site ORM Model

Sprint 2.9 - Multi-Site Management.

Sites are the primary multi-tenancy unit. Every integration, remote host,
and credential profile belongs to a site. Sites represent physical or
logical organizational units (offices, data centers, departments).
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Site(Base):
    """
    A site represents a physical or logical organizational unit.

    Sites group integrations, hosts, and credentials together.
    Each site has its own health status and can be independently managed.
    """

    __tablename__ = "sites"

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

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ------------------------------------------------------------------ #
    # Location                                                            #
    # ------------------------------------------------------------------ #

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Contact                                                             #
    # ------------------------------------------------------------------ #

    contact_name: Mapped[str | None] = mapped_column(
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
