"""
Mission Control Credential Profile API Schemas

Pydantic models for Credential Profile API endpoints.

Sprint 2.1.4 - Secure Credential Vault.

Responses never return sensitive fields (passwords, keys, passphrases).
All sensitive data is encrypted at rest and decrypted only in the
service layer immediately before use by providers.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CredentialProfileCreate(BaseModel):
    """Payload for creating a new credential profile."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the credential profile.",
        examples=["Production SSH Key"],
    )
    authentication_type: str = Field(
        default="password",
        max_length=20,
        description="Authentication method.",
        examples=["password", "ssh_key", "ntlm", "basic"],
    )
    username: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Username for authentication.",
        examples=["root"],
    )
    password: str | None = Field(
        default=None,
        description="Password for authentication (encrypted at rest).",
    )
    ssh_key: str | None = Field(
        default=None,
        description="SSH private key content (encrypted at rest).",
    )
    passphrase: str | None = Field(
        default=None,
        description="Passphrase for encrypted SSH keys (encrypted at rest).",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Description of the credential profile.",
    )


class CredentialProfileUpdate(BaseModel):
    """Payload for updating an existing credential profile."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated display name.",
    )
    authentication_type: str | None = Field(
        default=None,
        max_length=20,
        description="Updated authentication method.",
    )
    username: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated username.",
    )
    password: str | None = Field(
        default=None,
        description=(
            "Updated password. Empty string preserves existing. "
            "Non-empty replaces encrypted value."
        ),
    )
    ssh_key: str | None = Field(
        default=None,
        description=(
            "Updated SSH private key. Empty string preserves existing."
        ),
    )
    passphrase: str | None = Field(
        default=None,
        description=(
            "Updated passphrase for encrypted SSH keys. "
            "Empty string preserves existing."
        ),
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated description.",
    )


class CredentialProfileResponse(BaseModel):
    """Credential profile returned by the API.

    Never exposes sensitive fields: password, password_encrypted,
    private_key, private_key_encrypted, passphrase, passphrase_encrypted.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique credential profile identifier.",
    )
    name: str = Field(
        ...,
        description="Display name.",
    )
    authentication_type: str = Field(
        ...,
        description="Authentication method.",
    )
    username: str = Field(
        ...,
        description="Username.",
    )
    description: str | None = Field(
        default=None,
        description="Description.",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp.",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp.",
    )


class CredentialProfileListResponse(BaseModel):
    """List of credential profiles."""

    count: int = Field(
        ...,
        description="Total number of credential profiles returned.",
    )
    items: list[CredentialProfileResponse] = Field(
        ...,
        description="Credential profile records.",
    )
