"""
Mission Control Playbook Variable API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class PlaybookVariableCreate(BaseModel):
    """Payload for creating a playbook variable."""

    name: str = Field(..., min_length=1, max_length=200)
    value: str | None = Field(default=None)
    variable_type: str = Field(default="string", max_length=30)
    description: str | None = Field(default=None, max_length=1000)
    required: bool = Field(default=False)
    sensitive: bool = Field(default=False)
    default_value: str | None = Field(default=None)


class PlaybookVariableUpdate(BaseModel):
    """Payload for updating a playbook variable."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    value: str | None = None
    variable_type: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, max_length=1000)
    required: bool | None = None
    sensitive: bool | None = None
    default_value: str | None = None


class PlaybookVariableResponse(BaseModel):
    """Response for a single playbook variable."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    name: str
    value: str | None
    variable_type: str
    description: str | None
    required: bool
    sensitive: bool
    default_value: str | None
    created_at: datetime
    updated_at: datetime


class PlaybookVariableListResponse(BaseModel):
    """Response for listing playbook variables."""

    count: int
    items: list[PlaybookVariableResponse]
