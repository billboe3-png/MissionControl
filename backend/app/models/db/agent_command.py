"""
Mission Control Agent Command ORM Model

Sprint 2.7 - Mission Control Agent.

Stores commands dispatched to agents and their execution results.
Supports script execution, file transfers, and remote command execution.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AgentCommand(Base):
    """
    A command dispatched to an agent for execution.

    Commands are queued on the server side and picked up by agents
    during their polling cycle. Results are stored back when the
    agent reports completion.
    """

    __tablename__ = "agent_commands"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    command_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Execution Result                                                    #
    # ------------------------------------------------------------------ #

    stdout: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    stderr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    exit_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    success: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # File Transfer                                                       #
    # ------------------------------------------------------------------ #

    file_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    file_content_b64: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Metadata                                                            #
    # ------------------------------------------------------------------ #

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timeout: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )

    requested_by: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Timestamps                                                          #
    # ------------------------------------------------------------------ #

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
