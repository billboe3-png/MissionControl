"""
Mission Control Playbook Execution ORM Model

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.database import Base


class PlaybookExecution(Base):
    """Record of a playbook execution attempt."""

    __tablename__ = "playbook_executions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    playbook_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="live"
    )
    trigger_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="manual"
    )
    triggered_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    variables_used: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    steps_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    steps_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    steps_failed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    steps_skipped: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    output: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    rollback_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    rollback_output: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    approval_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    approval_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
