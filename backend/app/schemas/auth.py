"""
Mission Control Auth Schemas

Pydantic models for authentication requests/responses.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""

    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with token and user info."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 - field name, not a secret assignment
    user: "UserSummary"


class UserCreateRequest(BaseModel):
    """Create a new user."""

    email: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    role: str = "readonly"
    company_id: int | None = None
    site_id: int | None = None


class UserUpdateRequest(BaseModel):
    """Update a user."""

    display_name: str | None = None
    role: str | None = None
    enabled: bool | None = None
    company_id: int | None = None
    site_id: int | None = None


class UserSummary(BaseModel):
    """Compact user info for token response."""

    id: int
    email: str
    display_name: str
    role: str
    company_id: int | None = None
    site_id: int | None = None
    enabled: bool

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Full user response."""

    id: int
    email: str
    display_name: str
    role: str
    company_id: int | None = None
    site_id: int | None = None
    enabled: bool
    last_login: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    """Change password."""

    current_password: str
    new_password: str = Field(..., min_length=8)
