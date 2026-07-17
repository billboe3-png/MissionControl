"""
Mission Control Remote Host API Schemas

Pydantic models for Remote Host API endpoints.

Sprint 2.1.0 - Remote Operations Framework.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RemoteHostCreate(BaseModel):
    """Payload for creating a new remote host."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the remote host.",
        examples=["WebServer01"],
    )
    hostname: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Hostname or FQDN of the remote host.",
        examples=["web01.company.com"],
    )
    ip_address: str | None = Field(
        default=None,
        max_length=45,
        description="IP address of the remote host.",
        examples=["192.168.1.100"],
    )
    operating_system: str | None = Field(
        default=None,
        max_length=100,
        description="Operating system of the remote host.",
        examples=["Ubuntu 22.04", "Windows Server 2022"],
    )
    connection_type: str = Field(
        default="ssh",
        max_length=20,
        description="Connection protocol.",
        examples=["ssh", "winrm"],
    )
    port: int = Field(
        default=22,
        description="Connection port.",
        examples=[22, 5985],
    )
    enabled: bool = Field(
        default=True,
        description="Whether the host is enabled for connections.",
    )
    credential_profile_id: int | None = Field(
        default=None,
        description="ID of the credential profile to use.",
    )


class RemoteHostUpdate(BaseModel):
    """Payload for updating an existing remote host."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated display name.",
    )
    hostname: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Updated hostname.",
    )
    ip_address: str | None = Field(
        default=None,
        max_length=45,
        description="Updated IP address.",
    )
    operating_system: str | None = Field(
        default=None,
        max_length=100,
        description="Updated operating system.",
    )
    connection_type: str | None = Field(
        default=None,
        max_length=20,
        description="Updated connection protocol.",
    )
    port: int | None = Field(
        default=None,
        description="Updated connection port.",
    )
    enabled: bool | None = Field(
        default=None,
        description="Updated enabled status.",
    )
    credential_profile_id: int | None = Field(
        default=None,
        description="Updated credential profile ID.",
    )


class RemoteHostResponse(BaseModel):
    """Remote host returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique remote host identifier.",
    )
    name: str = Field(
        ...,
        description="Display name of the remote host.",
    )
    hostname: str = Field(
        ...,
        description="Hostname or FQDN.",
    )
    ip_address: str | None = Field(
        default=None,
        description="IP address.",
    )
    operating_system: str | None = Field(
        default=None,
        description="Operating system.",
    )
    connection_type: str = Field(
        ...,
        description="Connection protocol.",
    )
    port: int = Field(
        ...,
        description="Connection port.",
    )
    enabled: bool = Field(
        ...,
        description="Whether the host is enabled.",
    )
    credential_profile_id: int | None = Field(
        default=None,
        description="ID of the credential profile.",
    )
    credential_profile_name: str | None = Field(
        default=None,
        description="Name of the credential profile.",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp.",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp.",
    )


class RemoteHostListResponse(BaseModel):
    """List of remote hosts."""

    count: int = Field(
        ...,
        description="Total number of remote hosts returned.",
    )
    items: list[RemoteHostResponse] = Field(
        ...,
        description="Remote host records.",
    )
