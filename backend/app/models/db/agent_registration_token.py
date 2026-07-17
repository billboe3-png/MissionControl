"""
Mission Control Agent Registration Token Model

Sprint 2.9 - Agent Registration with Company/Site scoping.

Registration tokens encode which company and site an agent belongs to.
Tokens expire after a configurable period and can only be used a limited
number of times.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AgentRegistrationToken(Base):
    """A registration token that assigns company/site to new agents."""

    __tablename__ = "agent_registration_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Tenant scoping                                                      #
    # ------------------------------------------------------------------ #

    company_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    site_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Limits                                                              #
    # ------------------------------------------------------------------ #

    max_agents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ------------------------------------------------------------------ #
    # Metadata                                                            #
    # ------------------------------------------------------------------ #

    label: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
