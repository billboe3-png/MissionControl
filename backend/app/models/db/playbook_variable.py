"""
Mission Control Playbook Variable ORM Model

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


class PlaybookVariable(Base):
    """A named variable that can be used within playbook steps."""

    __tablename__ = "playbook_variables"

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
    value: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    variable_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="string"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    sensitive: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    default_value: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
