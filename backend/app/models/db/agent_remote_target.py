"""
Mission Control Agent Remote Target ORM Model

Stores remote machines that an agent can reach inside its network
and relay data back to the server (Zabbix proxy model).
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AgentRemoteTarget(Base):
    """
    A remote machine that an agent monitors and relays data from.

    The agent connects to this target via PS Remoting, SSH, or WinRM,
    collects inventory data, and sends it back to the server.
    """

    __tablename__ = "agent_remote_targets"

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

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    hostname: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    protocol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="psremoting",
    )

    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5985,
    )

    username: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    password_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ssh_key_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    tags: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    target_plugins: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated plugin identifiers enabled for this remote target.",
    )

    db_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="postgresql",
        comment="Veeam backing database: postgresql or mssql.",
    )

    column_case: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pascal",
        comment="Veeam SQL column case: pascal or snake (MSSQL).",
    )

    last_collected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unknown",
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
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
