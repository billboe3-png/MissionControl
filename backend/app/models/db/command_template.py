"""
Mission Control Command Template ORM Model

Sprint 2.1.8 - Remote Operations Finalization.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.database import Base


class CommandTemplate(Base):
    """Reusable command template for remote operations."""

    __tablename__ = "command_templates"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    protocol: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ssh"
    )
    command: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
