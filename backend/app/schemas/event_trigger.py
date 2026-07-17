"""
Mission Control Event Trigger API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventTriggerCreate(BaseModel):
    """Payload for creating an event trigger."""

    name: str = Field(..., min_length=1, max_length=200)
    event_type: str = Field(..., min_length=1, max_length=50)
    conditions: str | None = Field(default=None)
    enabled: bool = Field(default=True)


class EventTriggerUpdate(BaseModel):
    """Payload for updating an event trigger."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    event_type: str | None = Field(default=None, min_length=1, max_length=50)
    conditions: str | None = None
    enabled: bool | None = None


class EventTriggerResponse(BaseModel):
    """Response for a single event trigger."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    name: str
    event_type: str
    conditions: str | None
    enabled: bool
    last_triggered: datetime | None
    trigger_count: int
    created_at: datetime
    updated_at: datetime


class EventTriggerListResponse(BaseModel):
    """Response for listing event triggers."""

    count: int
    items: list[EventTriggerResponse]
