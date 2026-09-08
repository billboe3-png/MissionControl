"""
Mission Control Agent Remote Target Schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class RemoteTargetCreate(BaseModel):
    name: str
    hostname: str
    protocol: str = "psremoting"
    port: int | None = None
    username: str
    password: str | None = None
    ssh_key: str | None = None
    enabled: bool = True
    tags: str | None = None
    notes: str | None = None
    target_plugins: str | None = None
    db_type: str = Field("postgresql", pattern="^(postgresql|mssql)$")
    column_case: str = Field("pascal", pattern="^(pascal|snake)$")


class RemoteTargetUpdate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    protocol: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    ssh_key: str | None = None
    enabled: bool | None = None
    tags: str | None = None
    notes: str | None = None
    target_plugins: str | None = None
    db_type: str | None = Field(None, pattern="^(postgresql|mssql)$")
    column_case: str | None = Field(None, pattern="^(pascal|snake)$")


class RemoteTargetResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    hostname: str
    protocol: str
    port: int
    username: str
    enabled: bool
    tags: str | None = None
    notes: str | None = None
    last_collected_at: datetime | None = None
    last_status: str
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime

    target_plugins: str | None = None
    db_type: str
    column_case: str

    model_config = {"from_attributes": True}


class AgentRemoteTargetsResponse(BaseModel):
    agent_id: int
    agent_name: str
    targets: list[RemoteTargetResponse]
