"""
Mission Control Task API Schemas

Pydantic models for Task API endpoints.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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
    assignee: str | None = Field(
        default=None,
        max_length=200,
        description="Person or system responsible.",
        examples=["Robert Barnes"],
    )
    due_date: date | None = Field(
        default=None,
        description="Due date for the task.",
        examples=["2026-08-24"],
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
        examples=["high"],
    )
    assignee: str | None = Field(
        default=None,
        max_length=200,
        description="Updated assignee.",
        examples=["Robert Barnes"],
    )
    due_date: date | None = Field(
        default=None,
        description="Updated due date.",
        examples=["2026-08-24"],
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
    assignee: str | None = Field(
        default=None,
        description="Person or system responsible for this task.",
        examples=["Robert Barnes"],
    )
    due_date: date | None = Field(
        default=None,
        description="Due date for the task.",
        examples=["2026-08-24"],
    )
    started_at: datetime | None = Field(
        default=None,
        description="When work on this task began.",
        examples=["2026-08-21T09:00:00"],
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When this task was marked completed.",
        examples=["2026-08-21T12:00:00"],
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
