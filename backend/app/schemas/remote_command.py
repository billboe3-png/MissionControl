"""
Mission Control Remote Command API Schemas

Pydantic models for remote command execution and history endpoints.

Sprint 2.1.0 - Remote Operations Framework.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RemoteTestConnectionRequest(BaseModel):
    """Payload for testing a remote connection."""

    host_id: int = Field(
        ...,
        description="ID of the remote host to test.",
    )


class RemoteTestConnectionResponse(BaseModel):
    """Result of a connection test."""

    success: bool = Field(
        ...,
        description="Whether the connection test succeeded.",
    )
    latency_ms: int = Field(
        ...,
        description="Connection latency in milliseconds.",
    )
    message: str = Field(
        ...,
        description="Human-readable result message.",
    )
    host: str = Field(
        ...,
        description="Display name of the host tested.",
    )
    connection_type: str = Field(
        ...,
        description="Connection protocol used.",
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp of the test.",
    )


class RemoteExecuteRequest(BaseModel):
    """Payload for executing a command on a remote host."""

    host_id: int = Field(
        ...,
        description="ID of the remote host to execute on.",
    )
    command: str = Field(
        ...,
        min_length=1,
        description="Command to execute.",
        examples=["hostname", "Get-Process"],
    )
    shell: str = Field(
        default="bash",
        max_length=20,
        description="Shell to execute the command in.",
        examples=["bash", "powershell", "cmd"],
    )


class RemoteExecuteResponse(BaseModel):
    """Result of a command execution."""

    host: str = Field(
        ...,
        description="Display name of the host.",
    )
    connection_type: str = Field(
        ...,
        description="Connection protocol used.",
    )
    command: str = Field(
        ...,
        description="Command that was executed.",
    )
    stdout: str = Field(
        ...,
        description="Standard output from the command.",
    )
    stderr: str = Field(
        ...,
        description="Standard error from the command.",
    )
    exit_code: int = Field(
        ...,
        description="Process exit code.",
    )
    success: bool = Field(
        ...,
        description="Whether the command succeeded.",
    )
    duration_ms: int = Field(
        ...,
        description="Execution duration in milliseconds.",
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp of the execution.",
    )


class CommandHistoryItem(BaseModel):
    """A single command history record."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique history record identifier.",
    )
    host_id: int = Field(
        ...,
        description="ID of the remote host.",
    )
    host_name: str | None = Field(
        default=None,
        description="Display name of the remote host.",
    )
    command: str = Field(
        ...,
        description="Command that was executed.",
    )
    shell: str = Field(
        ...,
        description="Shell used.",
    )
    stdout: str | None = Field(
        default=None,
        description="Standard output.",
    )
    stderr: str | None = Field(
        default=None,
        description="Standard error.",
    )
    exit_code: int | None = Field(
        default=None,
        description="Process exit code.",
    )
    success: bool = Field(
        ...,
        description="Whether the command succeeded.",
    )
    duration_ms: int | None = Field(
        default=None,
        description="Execution duration in milliseconds.",
    )
    started_at: datetime = Field(
        ...,
        description="When the command was started.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When the command completed.",
    )
    executed_by: str | None = Field(
        default=None,
        description="Who executed the command.",
    )


class RemoteHistoryResponse(BaseModel):
    """List of command history records."""

    count: int = Field(
        ...,
        description="Total number of history records returned.",
    )
    items: list[CommandHistoryItem] = Field(
        ...,
        description="Command history records.",
    )
