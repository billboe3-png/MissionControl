"""
Mission Control Playbook Schedule API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaybookScheduleCreate(BaseModel):
    """Payload for creating a playbook schedule."""

    name: str = Field(..., min_length=1, max_length=200)
    cron_expression: str = Field(..., min_length=1, max_length=100)
    enabled: bool = Field(default=True)
    variables_override: str | None = Field(default=None)


class PlaybookScheduleUpdate(BaseModel):
    """Payload for updating a playbook schedule."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    cron_expression: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool | None = None
    variables_override: str | None = None


class PlaybookScheduleResponse(BaseModel):
    """Response for a single playbook schedule."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    name: str
    cron_expression: str
    enabled: bool
    variables_override: str | None
    last_run: datetime | None
    next_run: datetime | None
    created_at: datetime
    updated_at: datetime


class PlaybookScheduleListResponse(BaseModel):
    """Response for listing playbook schedules."""

    count: int
    items: list[PlaybookScheduleResponse]
