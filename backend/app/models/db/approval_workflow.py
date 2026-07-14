"""
Mission Control Approval Workflow ORM Model

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


class ApprovalWorkflow(Base):
    """Approval workflow configuration for a playbook."""

    __tablename__ = "approval_workflows"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    playbook_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    required_approvers: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    approver_roles: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    auto_approve_on_timeout: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    timeout_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
