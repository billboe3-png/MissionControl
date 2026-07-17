"""
Mission Control Playbook Step API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaybookStepCreate(BaseModel):
    """Payload for creating a playbook step."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    step_type: str = Field(..., max_length=50)
    provider: str = Field(default="ssh", max_length=50)
    command: str = Field(..., min_length=1)
    target_host: str | None = Field(default=None, max_length=500)
    shell: str | None = Field(default=None, max_length=20)
    working_directory: str | None = Field(default=None, max_length=500)
    environment_variables: str | None = Field(default=None)
    timeout_seconds: int = Field(default=300, ge=1)
    retry_count: int = Field(default=0, ge=0)
    continue_on_failure: bool = Field(default=False)
    rollback_command: str | None = Field(default=None)
    step_order: int = Field(default=0, ge=0)


class PlaybookStepUpdate(BaseModel):
    """Payload for updating a playbook step."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    step_type: str | None = Field(default=None, max_length=50)
    provider: str | None = Field(default=None, max_length=50)
    command: str | None = Field(default=None, min_length=1)
    target_host: str | None = Field(default=None, max_length=500)
    shell: str | None = Field(default=None, max_length=20)
    working_directory: str | None = Field(default=None, max_length=500)
    environment_variables: str | None = None
    timeout_seconds: int | None = Field(default=None, ge=1)
    retry_count: int | None = Field(default=None, ge=0)
    continue_on_failure: bool | None = None
    rollback_command: str | None = None
    step_order: int | None = Field(default=None, ge=0)


class PlaybookStepResponse(BaseModel):
    """Response for a single playbook step."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    name: str
    description: str | None
    step_type: str
    provider: str
    command: str
    target_host: str | None
    shell: str | None
    working_directory: str | None
    environment_variables: str | None
    timeout_seconds: int
    retry_count: int
    continue_on_failure: bool
    rollback_command: str | None
    step_order: int
    created_at: datetime
    updated_at: datetime


class PlaybookStepListResponse(BaseModel):
    """Response for listing playbook steps."""

    count: int
    items: list[PlaybookStepResponse]
