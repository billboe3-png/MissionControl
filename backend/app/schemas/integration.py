"""
Mission Control Integration Schemas

Pydantic request/response models for integration management.
Secrets are NEVER exposed through the API after save.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ------------------------------------------------------------------ #
# Create / Update                                                     #
# ------------------------------------------------------------------ #


class IntegrationProfileCreate(BaseModel):
    """Request body for creating an integration profile."""

    name: str = Field(..., min_length=1, max_length=200)
    integration_type: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    enabled: bool = False
    agent_id: int | None = None

    base_url: str | None = None
    username: str | None = None
    password: str | None = None

    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    authority_url: str | None = None

    domain: str | None = None
    base_dn: str | None = None
    use_ssl: bool = True

    ssh_host: str | None = None
    ssh_port: int = 22
    ssh_username: str | None = None
    ssh_password: str | None = None

    data_source: str = "both"

    verify_ssl: bool = True
    timeout: int = 30
    poll_interval: int = 60


class IntegrationProfileUpdate(BaseModel):
    """Request body for updating an integration profile."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    enabled: bool | None = None
    agent_id: int | None = None

    base_url: str | None = None
    username: str | None = None
    password: str | None = None

    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    authority_url: str | None = None

    domain: str | None = None
    base_dn: str | None = None
    use_ssl: bool | None = None

    ssh_host: str | None = None
    ssh_port: int | None = None
    ssh_username: str | None = None
    ssh_password: str | None = None

    data_source: str | None = None

    verify_ssl: bool | None = None
    timeout: int | None = None
    poll_interval: int | None = None


# ------------------------------------------------------------------ #
# Response                                                            #
# ------------------------------------------------------------------ #


class IntegrationProfileResponse(BaseModel):
    """Response for an integration profile. Secrets are masked."""

    id: int
    name: str
    integration_type: str
    description: str | None = None
    enabled: bool
    agent_id: int | None = None

    base_url: str | None = None
    username: str | None = None

    tenant_id: str | None = None
    client_id: str | None = None
    authority_url: str | None = None

    domain: str | None = None
    base_dn: str | None = None
    use_ssl: bool = True

    ssh_host: str | None = None
    ssh_port: int = 22
    ssh_username: str | None = None
    has_ssh_password: bool = False

    data_source: str = "both"

    verify_ssl: bool = True
    timeout: int = 30
    poll_interval: int = 60

    last_test: datetime | None = None
    last_success: datetime | None = None
    last_error: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class IntegrationProfileListResponse(BaseModel):
    """Response for listing integration profiles."""

    count: int
    items: list[IntegrationProfileResponse]


# ------------------------------------------------------------------ #
# Test Connection                                                     #
# ------------------------------------------------------------------ #


class IntegrationTestResponse(BaseModel):
    """Response for a connection test."""

    success: bool
    latency_ms: int | None = None
    message: str | None = None
    version: str | None = None
    error: str | None = None
    details: dict | None = None
