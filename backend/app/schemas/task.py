"""
Mission Control Task API Schemas

Pydantic models for Task API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class TaskCreate(BaseModel):
    """Payload for creating a new task."""

    project_id: int = Field(
        ...,
        description="Identifier of the parent project.",
        examples=[1],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short task title.",
        examples=["Wire dashboard to PostgreSQL"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional task description.",
        examples=["Connect dashboard services to live database queries."],
    )
    status: str = Field(
        default="pending",
        max_length=50,
        description="Current task status.",
        examples=["pending"],
    )
    priority: str = Field(
        default="medium",
        max_length=50,
        description="Task priority level.",
        examples=["medium"],
    )


class TaskUpdate(BaseModel):
    """Payload for updating an existing task."""

    project_id: int | None = Field(
        default=None,
        description="Updated parent project identifier.",
        examples=[2],
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated task title.",
        examples=["Updated task title"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated task description.",
        examples=["Updated task description."],
    )
    status: str | None = Field(
        default=None,
        max_length=50,
        description="Updated task status.",
        examples=["completed"],
    )
    priority: str | None = Field(
        default=None,
        max_length=50,
        description="Updated task priority.",
        examples=["low"],
    )


class TaskResponse(BaseModel):
    """Task returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique task identifier.",
        examples=[1],
    )
    project_id: int = Field(
        ...,
        description="Identifier of the parent project.",
        examples=[1],
    )
    title: str = Field(
        ...,
        description="Short task title.",
        examples=["Wire dashboard to PostgreSQL"],
    )
    description: str | None = Field(
        default=None,
        description="Optional task description.",
        examples=["Connect dashboard services to live database queries."],
    )
    status: str = Field(
        ...,
        description="Current task status.",
        examples=["in_progress"],
    )
    priority: str = Field(
        ...,
        description="Task priority level.",
        examples=["high"],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the task was created.",
        examples=["2026-07-08T13:00:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the task was last updated.",
        examples=["2026-07-08T13:00:00"],
    )


class TaskListResponse(BaseModel):
    """Paginated-style list of tasks."""

    count: int = Field(
        ...,
        description="Total number of tasks returned.",
        examples=[8],
    )
    items: list[TaskResponse] = Field(
        ...,
        description="Task records.",
    )
