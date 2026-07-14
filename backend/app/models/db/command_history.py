"""
Mission Control Command History ORM Model

Sprint 2.1.8 - Remote Operations Finalization.
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


class CommandHistory(Base):
    """Record of a command executed on a remote host."""

    __tablename__ = "command_history"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
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
    command: Mapped[str] = mapped_column(Text, nullable=False)
    shell: Mapped[str] = mapped_column(
        String(20), nullable=False, default="bash"
    )
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    executed_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    username: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    working_directory: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    execution_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual"
    )
