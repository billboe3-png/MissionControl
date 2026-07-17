"""
Mission Control Company Schemas

Pydantic request/response models for company management.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    """Request body for creating a company."""

    name: str = Field(..., min_length=1, max_length=200)
    display_name: str = Field(..., min_length=1, max_length=200)
    status: str = Field("active", max_length=20)
    license_type: str | None = None
    max_sites: int = 10
    max_agents: int = 100
    max_users: int = 50
    primary_contact: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    timezone: str | None = None
    logo_url: str | None = None
    theme: str | None = None
    notes: str | None = None
    enabled: bool = True


class CompanyUpdate(BaseModel):
    """Request body for updating a company."""

    name: str | None = Field(None, min_length=1, max_length=200)
    display_name: str | None = Field(None, min_length=1, max_length=200)
    status: str | None = None
    license_type: str | None = None
    max_sites: int | None = None
    max_agents: int | None = None
    max_users: int | None = None
    primary_contact: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    timezone: str | None = None
    logo_url: str | None = None
    theme: str | None = None
    notes: str | None = None
    enabled: bool | None = None


class CompanyResponse(BaseModel):
    """Response for a company."""

    id: int
    uuid: str
    name: str
    display_name: str
    status: str
    license_type: str | None = None
    max_sites: int
    max_agents: int
    max_users: int
    primary_contact: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    timezone: str | None = None
    logo_url: str | None = None
    theme: str | None = None
    notes: str | None = None
    enabled: bool
    is_global: bool

    site_count: int = 0
    agent_count: int = 0
    integration_count: int = 0

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """Response for listing companies."""

    count: int
    items: list[CompanyResponse]


class CompanySummaryResponse(BaseModel):
    """Compact response for company selector dropdown."""

    id: int
    uuid: str
    name: str
    display_name: str
    status: str
    enabled: bool

    model_config = {"from_attributes": True}
