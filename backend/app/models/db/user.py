"""
Mission Control User ORM Model

Sprint 2.9 - Multi-Tenant & Multi-Site Platform.

Users belong to companies and optionally to sites.
Roles control what users can see and do.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    """A user account with company/site scoping and role-based access."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    site_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Identity                                                            #
    # ------------------------------------------------------------------ #

    email: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # Authorization                                                       #
    # ------------------------------------------------------------------ #

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="readonly",
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Status                                                              #
    # ------------------------------------------------------------------ #

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ------------------------------------------------------------------ #
    # Metadata                                                            #
    # ------------------------------------------------------------------ #

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
