"""
Mission Control Note API Schemas

Pydantic models for Note API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    """Payload for creating a new note."""

    project_id: int = Field(
        ...,
        description="Identifier of the parent project.",
        examples=[1],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short note title.",
        examples=["Meeting Notes"],
    )
    content: str = Field(
        ...,
        description="Note body content.",
        examples=["Discussed deployment timeline."],
    )


class NoteUpdate(BaseModel):
    """Payload for updating an existing note."""

    project_id: int | None = Field(
        default=None,
        description="Updated parent project identifier.",
        examples=[2],
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated note title.",
        examples=["Updated Meeting Notes"],
    )
    content: str | None = Field(
        default=None,
        description="Updated note body content.",
        examples=["Updated content."],
    )


class NoteResponse(BaseModel):
    """Note returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique note identifier.",
        examples=[1],
    )
    title: str = Field(
        ...,
        description="Note title.",
        examples=["Operations runbook"],
    )
    content: str = Field(
        ...,
        description="Note body content.",
        examples=["Restart nginx after configuration changes."],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the note was created.",
        examples=["2026-07-08T13:00:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the note was last updated.",
        examples=["2026-07-08T13:00:00"],
    )


class NoteListResponse(BaseModel):
    """Paginated-style list of notes."""

    count: int = Field(
        ...,
        description="Total number of notes returned.",
        examples=[3],
    )
    items: list[NoteResponse] = Field(
        ...,
        description="Note records.",
    )
