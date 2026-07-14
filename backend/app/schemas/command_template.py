"""
Mission Control Command Template API Schemas

Sprint 2.1.8 - Remote Operations Finalization.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class CommandTemplateCreate(BaseModel):
    """Payload for creating a command template."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    protocol: str = Field(default="ssh", max_length=20)
    command: str = Field(..., min_length=1)
    category: str | None = Field(default=None, max_length=100)


class CommandTemplateUpdate(BaseModel):
    """Payload for updating a command template."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    protocol: str | None = Field(default=None, max_length=20)
    command: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, max_length=100)


class CommandTemplateResponse(BaseModel):
    """Response for a single command template."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    protocol: str
    command: str
    category: str | None
    created_at: datetime
    updated_at: datetime


class CommandTemplateListResponse(BaseModel):
    """Response for listing command templates."""

    count: int
    items: list[CommandTemplateResponse]
