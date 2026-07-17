"""
Mission Control Playbook Execution API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaybookExecuteRequest(BaseModel):
    """Request to execute a playbook."""

    mode: str = Field(default="live", max_length=20)
    triggered_by: str | None = Field(default=None, max_length=200)
    variables: dict[str, str] | None = Field(default=None)


class PlaybookExecuteResponse(BaseModel):
    """Response for a playbook execution."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    status: str
    mode: str
    trigger_type: str
    triggered_by: str | None
    variables_used: str | None
    steps_total: int
    steps_completed: int
    steps_failed: int
    steps_skipped: int
    output: str | None
    error: str | None
    rollback_status: str | None
    rollback_output: str | None
    approval_required: bool
    approval_status: str | None
    duration_ms: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class PlaybookExecutionListResponse(BaseModel):
    """Response for listing playbook executions."""

    count: int
    items: list[PlaybookExecuteResponse]


class DryRunRequest(BaseModel):
    """Request to dry-run a playbook."""

    variables: dict[str, str] | None = Field(default=None)


class DryRunResponse(BaseModel):
    """Response for a dry-run result."""

    execution_id: int
    status: str
    steps_validated: int
    steps_total: int
    output: str
    warnings: list[str]
    errors: list[str]


class RollbackRequest(BaseModel):
    """Request to rollback a playbook execution."""

    reason: str | None = Field(default=None, max_length=1000)


class RollbackResponse(BaseModel):
    """Response for a rollback operation."""

    execution_id: int
    rollback_status: str
    output: str | None
    error: str | None
