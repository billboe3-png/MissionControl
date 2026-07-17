"""
Mission Control Agent Registration Token Schemas

Pydantic models for token management.
Sprint 2.9 - Agent Registration with Company/Site scoping.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TokenCreateRequest(BaseModel):
    """Create a new registration token."""

    company_id: int | None = None
    site_id: int | None = None
    max_agents: int = Field(10, ge=1, le=1000)
    label: str | None = Field(None, max_length=200)
    expires_hours: int | None = Field(None, ge=1, le=8760)


class TokenResponse(BaseModel):
    """Response for a registration token."""

    id: int
    token: str
    company_id: int | None = None
    site_id: int | None = None
    max_agents: int
    used_count: int
    label: str | None = None
    expires_at: datetime | None = None
    enabled: bool
    created_at: datetime | None = None
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}
