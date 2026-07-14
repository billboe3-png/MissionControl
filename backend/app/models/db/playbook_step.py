"""
Mission Control Playbook Step ORM Model

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


class PlaybookStep(Base):
    """A single step within a playbook execution plan."""

    __tablename__ = "playbook_steps"

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
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    step_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ssh"
    )
    command: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    target_host: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    shell: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    working_directory: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    environment_variables: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=300
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    continue_on_failure: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    rollback_command: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    step_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
