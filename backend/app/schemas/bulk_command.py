"""
Mission Control Bulk Command API Schemas

Sprint 2.1.8 - Remote Operations Finalization.
"""

from pydantic import BaseModel, Field


class BulkExecuteRequest(BaseModel):
    """Payload for executing a command on multiple hosts."""

    host_ids: list[int] = Field(..., min_length=1, description="List of host IDs.")
    command: str = Field(..., min_length=1)
    shell: str = Field(default="bash", max_length=20)


class BulkExecuteResult(BaseModel):
    """Result for a single host in a bulk execution."""

    host_id: int
    host_name: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class BulkExecuteResponse(BaseModel):
    """Response for bulk command execution."""

    total: int
    succeeded: int
    failed: int
    results: list[BulkExecuteResult]


class SessionMetricsResponse(BaseModel):
    """Provider and session metrics."""

    active_ssh_sessions: int
    active_winrm_sessions: int
    connection_pool_size: int
    connection_pool_used: int
    average_latency_ms: float
    total_commands_executed: int
    total_commands_failed: int
    last_activity: str | None = None
