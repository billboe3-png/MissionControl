"""
Mission Control Project API Schemas

Pydantic models for Project CRUD endpoints.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the project.",
        examples=["Mission Control"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional project description.",
        examples=["Personal productivity platform for IT operations."],
    )
    active: bool = Field(
        default=True,
        description="Whether the project is active.",
        examples=[True],
    )


class ProjectUpdate(BaseModel):
    """Payload for updating an existing project."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated display name of the project.",
        examples=["UnitSphere"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated project description.",
        examples=["Unified infrastructure and automation platform."],
    )
    active: bool | None = Field(
        default=None,
        description="Updated active status of the project.",
        examples=[False],
    )


class ProjectResponse(BaseModel):
    """Project returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique project identifier.",
        examples=[1],
    )
    name: str = Field(
        ...,
        description="Display name of the project.",
        examples=["Mission Control"],
    )
    description: str | None = Field(
        default=None,
        description="Optional project description.",
        examples=["Personal productivity platform for IT operations."],
    )
    active: bool = Field(
        ...,
        description="Whether the project is active.",
        examples=[True],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the project was created.",
        examples=["2026-07-08T13:00:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the project was last updated.",
        examples=["2026-07-08T13:00:00"],
    )


class ProjectListResponse(BaseModel):
    """Paginated-style list of projects."""

    count: int = Field(
        ...,
        description="Total number of projects returned.",
        examples=[4],
    )
    items: list[ProjectResponse] = Field(
        ...,
        description="Project records.",
    )
