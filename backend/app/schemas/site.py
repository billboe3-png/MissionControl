"""
Mission Control Site Schemas

Pydantic request/response models for site management.
Sprint 2.9 - Multi-Site Management.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ------------------------------------------------------------------ #
# Create / Update                                                     #
# ------------------------------------------------------------------ #


class SiteCreate(BaseModel):
    """Request body for creating a site."""

    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=100)
    company_id: int | None = None
    description: str | None = None
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)
    enabled: bool = True
    is_default: bool = False

    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    timezone: str | None = None

    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class SiteUpdate(BaseModel):
    """Request body for updating a site."""

    name: str | None = Field(None, min_length=1, max_length=200)
    code: str | None = Field(None, min_length=1, max_length=100)
    company_id: int | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    enabled: bool | None = None
    is_default: bool | None = None

    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    timezone: str | None = None

    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


# ------------------------------------------------------------------ #
# Response                                                            #
# ------------------------------------------------------------------ #


class SiteResponse(BaseModel):
    """Response for a site."""

    id: int
    name: str
    code: str
    company_id: int | None = None
    company_name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    enabled: bool
    is_default: bool

    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    timezone: str | None = None

    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

    integration_count: int = 0
    host_count: int = 0

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SiteListResponse(BaseModel):
    """Response for listing sites."""

    count: int
    items: list[SiteResponse]


class SiteSummaryResponse(BaseModel):
    """Compact response for site selector dropdown."""

    id: int
    name: str
    code: str
    color: str | None = None
    icon: str | None = None
    enabled: bool

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Health                                                              #
# ------------------------------------------------------------------ #


class SiteHealthResponse(BaseModel):
    """Site health status."""

    site_id: int
    site_name: str
    site_code: str
    health: str
    integration_count: int = 0
    enabled_integrations: int = 0
    host_count: int = 0
    enabled_hosts: int = 0
    issues: list[str] = []
