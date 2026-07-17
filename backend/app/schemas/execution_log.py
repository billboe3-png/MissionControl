"""
Mission Control Execution Log API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExecutionLogResponse(BaseModel):
    """Response for a single execution log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: int
    step_id: int | None
    level: str
    message: str
    stdout: str | None
    stderr: str | None
    exit_code: int | None
    duration_ms: int | None
    timestamp: datetime


class ExecutionLogListResponse(BaseModel):
    """Response for listing execution logs."""

    count: int
    items: list[ExecutionLogResponse]
