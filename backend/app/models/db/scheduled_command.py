"""
Mission Control Scheduled Command ORM Model

Sprint 2.1.8 - Remote Operations Finalization.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ScheduledCommand(Base):
    """A command scheduled to run periodically on a remote host."""

    __tablename__ = "scheduled_commands"

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

    host_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("remote_hosts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credential_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("credential_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    command: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    cron_expression: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    last_run: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    next_run: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
