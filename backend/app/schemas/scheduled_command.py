"""
Mission Control Scheduled Command API Schemas

Sprint 2.1.8 - Remote Operations Finalization.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ScheduledCommandCreate(BaseModel):
    """Payload for creating a scheduled command."""

    host_id: int = Field(..., description="Target host ID.")
    credential_id: int | None = Field(
        default=None, description="Credential profile ID."
    )
    command: str = Field(..., min_length=1)
    cron_expression: str = Field(
        ..., min_length=1, max_length=100,
        description="Cron expression (e.g. '0 */6 * * *').",
    )
    enabled: bool = Field(default=True)


class ScheduledCommandUpdate(BaseModel):
    """Payload for updating a scheduled command."""

    command: str | None = Field(default=None, min_length=1)
    cron_expression: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    enabled: bool | None = None


class ScheduledCommandResponse(BaseModel):
    """Response for a single scheduled command."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    host_name: str | None = None
    credential_id: int | None
    command: str
    cron_expression: str
    enabled: bool
    last_run: datetime | None
    next_run: datetime | None
    created_at: datetime
    updated_at: datetime


class ScheduledCommandListResponse(BaseModel):
    """Response for listing scheduled commands."""

    count: int
    items: list[ScheduledCommandResponse]
