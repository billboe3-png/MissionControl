"""
Mission Control Execution Log ORM Model

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ExecutionLog(Base):
    """Detailed log entry for a playbook execution step."""

    __tablename__ = "execution_logs"

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

    execution_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("playbook_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("playbook_steps.id", ondelete="SET NULL"),
        nullable=True,
    )
    level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info"
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    stdout: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    stderr: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    exit_code: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
