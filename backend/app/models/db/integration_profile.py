"""
Mission Control Integration Profile ORM Model

Sprint 2.3.1 - Integration Management (Production Configuration UI).

Stores configuration for external integrations (Zabbix, Active Directory,
Microsoft 365, and future systems). Secrets are encrypted at rest using
Fernet symmetric encryption via CredentialCipher.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IntegrationProfile(Base):
    """
    Configuration profile for an external integration.

    Each row represents one configured integration instance.
    Sensitive fields (secrets, tokens, passwords) are encrypted
    at rest. The service layer handles encryption/decryption
    transparently. The API never exposes decrypted values.
    """

    __tablename__ = "integration_profiles"

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

    agent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Connection                                                          #
    # ------------------------------------------------------------------ #

    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    encrypted_secret: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Microsoft 365 / OAuth                                               #
    # ------------------------------------------------------------------ #

    tenant_id: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    client_id: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    client_secret_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    authority_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Active Directory / LDAP                                             #
    # ------------------------------------------------------------------ #

    domain: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    base_dn: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    use_ssl: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ------------------------------------------------------------------ #
    # SSH (for PowerShell bridge on Windows servers)                      #
    # ------------------------------------------------------------------ #

    ssh_host: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    ssh_port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=22,
    )

    ssh_username: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    ssh_password_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Data source mode (api / ssh / both)                                 #
    # ------------------------------------------------------------------ #

    data_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="both",
    )

    # ------------------------------------------------------------------ #
    # Settings                                                            #
    # ------------------------------------------------------------------ #

    verify_ssl: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    timeout: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    poll_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )

    # ------------------------------------------------------------------ #
    # Status                                                              #
    # ------------------------------------------------------------------ #

    last_test: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_success: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Timestamps                                                          #
    # ------------------------------------------------------------------ #

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
