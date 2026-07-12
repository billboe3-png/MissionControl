"""
Mission Control Credential Profile ORM Model

Sprint 2.1.0 - Remote Operations Framework.

NOTE: Passwords and keys remain plain text ONLY during Sprint 2.1.0.
Sprint 2.1.3 replaces this with encryption.
"""

from datetime import UTC
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.database import Base


class CredentialProfile(Base):
    """
    Stored credentials for connecting to remote machines.
    Supports password, SSH key, NTLM, and basic authentication.
    """

    __tablename__ = "credential_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    authentication_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="password",
    )

    username: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    password: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ssh_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
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
