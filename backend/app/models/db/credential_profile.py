"""
Mission Control Credential Profile ORM Model

Sprint 2.1.4 - Secure Credential Vault.

Stores credential data with encryption at rest.
Sensitive fields (password, ssh_key, passphrase) are encrypted
using Fernet symmetric encryption before persistence.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CredentialProfile(Base):
    """
    Stored credentials for connecting to remote machines.
    Supports password, SSH key, NTLM, and basic authentication.

    Sensitive fields are encrypted at rest using Fernet.
    The service layer handles encryption/decryption transparently.
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

    # Plaintext columns (kept for migration compatibility, will be NULL)
    password: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ssh_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Encrypted columns (Sprint 2.1.4)
    password_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    private_key_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    passphrase_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    key_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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
