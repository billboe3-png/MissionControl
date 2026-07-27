"""
Mission Control Agent Schemas

Pydantic request/response models for the Agent management API.
Handles registration, heartbeat, inventory, command dispatch,
and file transfer.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ------------------------------------------------------------------ #
# Registration                                                        #
# ------------------------------------------------------------------ #


class AgentRegisterRequest(BaseModel):
    """Payload for agent self-registration."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name for the agent.",
        examples=["webserver-01"],
    )
    hostname: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Hostname of the agent machine.",
        examples=["web01.corp.local"],
    )
    registration_token: str | None = Field(
        default=None,
        description="Registration token for company/site assignment.",
    )
    operating_system: str | None = Field(
        default=None,
        max_length=100,
        description="Operating system.",
    )
    os_version: str | None = Field(
        default=None,
        max_length=200,
        description="OS version string.",
    )
    ip_address: str | None = Field(
        default=None,
        max_length=45,
        description="IP address of the agent.",
    )
    agent_version: str | None = Field(
        default=None,
        max_length=50,
        description="Agent software version.",
    )
    tags: str | None = Field(
        default=None,
        max_length=500,
        description="Comma-separated tags.",
    )


class AgentRegisterResponse(BaseModel):
    """Response after successful agent registration."""

    agent_id: int = Field(
        ...,
        description="Unique agent identifier.",
    )
    api_key: str = Field(
        ...,
        description="API key for subsequent requests. Store securely.",
    )
    heartbeat_interval: int = Field(
        ...,
        description="Seconds between heartbeats.",
    )
    message: str = Field(
        default="Registration successful",
    )


# ------------------------------------------------------------------ #
# Heartbeat                                                           #
# ------------------------------------------------------------------ #


class AgentHeartbeatRequest(BaseModel):
    """Payload for agent heartbeat."""

    agent_id: int
    agent_version: str | None = None
    health: str = "healthy"
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    active_plugins: str | None = None


class AgentHeartbeatResponse(BaseModel):
    """Response to heartbeat including pending commands."""

    commands: list["AgentPendingCommand"] | None = None
    update_available: bool = False
    latest_version: str | None = None
    heartbeat_interval: int = 30
    remote_targets: list[dict] | None = None


class AgentPendingCommand(BaseModel):
    """A command pending for the agent to execute."""

    id: int
    command_type: str
    command: str
    timeout: int = 60
    file_path: str | None = None
    file_name: str | None = None
    file_content_b64: str | None = None


# ------------------------------------------------------------------ #
# Command Result                                                      #
# ------------------------------------------------------------------ #


class AgentCommandResultRequest(BaseModel):
    """Payload for reporting command execution result."""

    command_id: int
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    success: bool = False
    duration_ms: int | None = None
    error_message: str | None = None
    file_content_b64: str | None = None


class AgentCommandResultResponse(BaseModel):
    """Acknowledgement of command result receipt."""

    received: bool = True
    message: str = "Command result recorded"


# ------------------------------------------------------------------ #
# Command Dispatch (Server -> Agent via heartbeat)                     #
# ------------------------------------------------------------------ #


class AgentCommandDispatchRequest(BaseModel):
    """Payload for server to dispatch a command to an agent."""

    agent_id: int = Field(default=0, description="Set by router path parameter.")
    command_type: str = Field(
        ...,
        description="Type: execute, script, upload, download, inventory, update",
    )
    command: str = Field(
        ...,
        description="Command or script content.",
    )
    timeout: int = Field(default=60, ge=1, le=3600)
    file_path: str | None = None
    file_name: str | None = None
    file_content_b64: str | None = None
    requested_by: str | None = None


# ------------------------------------------------------------------ #
# CRUD                                                                #
# ------------------------------------------------------------------ #


class AgentCreate(BaseModel):
    """Manual agent creation (admin only)."""

    name: str = Field(..., min_length=1, max_length=200)
    hostname: str = Field(..., min_length=1, max_length=500)
    operating_system: str | None = None
    os_version: str | None = None
    ip_address: str | None = None
    enabled: bool = True
    tags: str | None = None
    notes: str | None = None


class AgentUpdate(BaseModel):
    """Update agent settings."""

    name: str | None = Field(None, min_length=1, max_length=200)
    enabled: bool | None = None
    tags: str | None = None
    notes: str | None = None
    heartbeat_interval: int | None = Field(None, ge=10, le=300)


class AgentResponse(BaseModel):
    """Agent returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    hostname: str
    status: str
    operating_system: str | None = None
    os_version: str | None = None
    ip_address: str | None = None
    agent_version: str | None = None
    enabled: bool
    health: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    last_heartbeat: datetime | None = None
    heartbeat_interval: int
    tags: str | None = None
    notes: str | None = None
    active_plugins: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    registered_at: datetime | None = None
    company_id: int | None = None


class AgentListResponse(BaseModel):
    """List of agents."""

    count: int
    online: int
    offline: int
    items: list[AgentResponse]


class AgentCommandResponse(BaseModel):
    """Agent command record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    command_type: str
    command: str
    status: str
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    success: bool | None = None
    duration_ms: int | None = None
    file_path: str | None = None
    file_name: str | None = None
    error_message: str | None = None
    timeout: int
    requested_by: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AgentCommandListResponse(BaseModel):
    """List of agent commands."""

    count: int
    items: list[AgentCommandResponse]


class AgentCommandHistoryResponse(BaseModel):
    """Command history for a specific agent."""

    agent_id: int
    agent_name: str
    count: int
    items: list[AgentCommandResponse]


class AgentInventoryResponse(BaseModel):
    """Current inventory for an agent."""

    agent_id: int
    agent_name: str
    hostname: str
    operating_system: str | None = None
    os_version: str | None = None
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    inventory: dict | None = None


# Fix forward reference
AgentHeartbeatResponse.model_rebuild()
