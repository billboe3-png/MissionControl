"""
Mission Control Playbook ORM Model

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Playbook(Base):
    """Automation playbook definition with versioning."""

    __tablename__ = "playbooks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
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
        String(200), nullable=False, unique=True
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    tags: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    auto_rollback: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3600
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
