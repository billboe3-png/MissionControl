"""
Mission Control Approval Request ORM Model

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.database import Base


class ApprovalRequest(Base):
    """Individual approval request for a playbook execution."""

    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    execution_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("playbook_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("approval_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    requested_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    comments: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
