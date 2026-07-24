"""
Mission Control Setup Schemas

Request/response models for the first-time setup wizard.
"""

from pydantic import BaseModel, EmailStr, Field


class SetupStatusResponse(BaseModel):
    """Whether the setup wizard is required."""

    setup_required: bool


class BootstrapRequest(BaseModel):
    """Company + Site + Admin creation in one request."""

    company_name: str = Field(..., min_length=1, max_length=200)
    company_code: str | None = Field(None, max_length=100)

    site_name: str = Field(..., min_length=1, max_length=200)
    site_timezone: str | None = Field(None, max_length=100)

    admin_display_name: str = Field(..., min_length=1, max_length=200)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=128)
    admin_confirm_password: str = Field(..., min_length=8, max_length=128)


class BootstrapResponse(BaseModel):
    """Result of a successful bootstrap."""

    company_id: int
    site_id: int
    admin_id: int
    message: str
