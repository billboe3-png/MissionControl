"""
Mission Control Remote Host ORM Model

Sprint 2.1.0 - Remote Operations Framework.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RemoteHost(Base):
    """
    A remote machine that Mission Control can connect to
    via SSH or WinRM for command execution.
    """

    __tablename__ = "remote_hosts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    site_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sites.id", ondelete="SET NULL"),
        nullable=True,
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

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    operating_system: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    connection_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ssh",
    )

    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=22,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    credential_profile_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("credential_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
