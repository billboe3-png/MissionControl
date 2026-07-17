"""
Mission Control Playbook API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaybookCreate(BaseModel):
    """Payload for creating a playbook."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=100)
    tags: str | None = Field(default=None, max_length=500)
    enabled: bool = Field(default=True)
    requires_approval: bool = Field(default=False)
    auto_rollback: bool = Field(default=False)
    timeout_seconds: int = Field(default=3600, ge=1)
    max_retries: int = Field(default=0, ge=0)
    created_by: str | None = Field(default=None, max_length=200)


class PlaybookUpdate(BaseModel):
    """Payload for updating a playbook."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=100)
    tags: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None
    requires_approval: bool | None = None
    auto_rollback: bool | None = None
    timeout_seconds: int | None = Field(default=None, ge=1)
    max_retries: int | None = Field(default=None, ge=0)


class PlaybookResponse(BaseModel):
    """Response for a single playbook."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    version: int
    category: str | None
    tags: str | None
    enabled: bool
    requires_approval: bool
    auto_rollback: bool
    timeout_seconds: int
    max_retries: int
    created_by: str | None
    created_at: datetime
    updated_at: datetime


class PlaybookListResponse(BaseModel):
    """Response for listing playbooks."""

    count: int
    items: list[PlaybookResponse]
