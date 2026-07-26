"""
Mission Control Plugin Schemas

Pydantic request/response models for plugin management.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExecutionTarget(StrEnum):
    """Plugin execution target."""
    SERVER = "server"
    AGENT = "agent"
    HYBRID = "hybrid"


class PluginStatus(StrEnum):
    """Plugin lifecycle status."""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


# ------------------------------------------------------------------ #
# Manifest (from plugin.json)                                         #
# ------------------------------------------------------------------ #


class PluginManifest(BaseModel):
    """Plugin manifest schema — validated from plugin.json."""

    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    version: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    author: str | None = Field(None, max_length=200)
    execution_target: ExecutionTarget
    category: str | None = Field(None, max_length=100)
    min_core_version: str | None = Field(None, max_length=50)
    permissions: list[str] = []
    dependencies: list[str] = []
    capabilities: list[str] = []


# ------------------------------------------------------------------ #
# Create / Update                                                     #
# ------------------------------------------------------------------ #


class PluginCreate(BaseModel):
    """Request body for registering a plugin."""

    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    name: str = Field(..., min_length=1, max_length=200)
    version: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    author: str | None = None
    execution_target: ExecutionTarget
    category: str | None = None
    min_core_version: str | None = None
    permissions: list[str] = []
    dependencies: list[str] = []
    capabilities: list[str] = []
    config: dict | None = None


class PluginUpdate(BaseModel):
    """Request body for updating a plugin."""

    name: str | None = Field(None, min_length=1, max_length=200)
    version: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = None
    author: str | None = None
    category: str | None = None
    min_core_version: str | None = None
    permissions: list[str] | None = None
    dependencies: list[str] | None = None
    capabilities: list[str] | None = None
    config: dict | None = None


# ------------------------------------------------------------------ #
# Response                                                            #
# ------------------------------------------------------------------ #


class PluginResponse(BaseModel):
    """Response for a single plugin."""

    id: int
    slug: str
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    execution_target: str
    category: str | None = None
    enabled: bool
    status: str
    config: dict | None = None
    capabilities: list[str] = []
    min_core_version: str | None = None
    permissions: list[str] = []
    dependencies: list[str] = []
    last_heartbeat: datetime | None = None
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PluginListResponse(BaseModel):
    """Response for listing plugins."""

    count: int
    items: list[PluginResponse]


# ------------------------------------------------------------------ #
# Actions                                                             #
# ------------------------------------------------------------------ #


class PluginActionResponse(BaseModel):
    """Response for a plugin lifecycle action."""

    slug: str
    status: str
    message: str


# ------------------------------------------------------------------ #
# Marketplace                                                         #
# ------------------------------------------------------------------ #


class PluginMarketplaceEntry(BaseModel):
    """Plugin listing in the marketplace."""

    slug: str
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    execution_target: str
    category: str | None = None
    permissions: list[str] = []
    dependencies: list[str] = []
    installed: bool = False
    enabled: bool = False
    status: str | None = None
