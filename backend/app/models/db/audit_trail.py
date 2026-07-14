"""
Mission Control Audit Trail ORM Model

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.database import Base


class AuditTrail(Base):
    """Immutable audit record for all automation actions."""

    __tablename__ = "audit_trail"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    entity_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    actor: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    details: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )
