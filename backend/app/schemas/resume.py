"""
Mission Control Resume API Schemas

Pydantic models for Resume API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreate(BaseModel):
    """Payload for creating a new resume entry."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Resume title.",
        examples=["Senior IT Operations Engineer"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Resume description.",
        examples=["10 years of IT operations experience."],
    )
    available: bool = Field(
        default=True,
        description="Whether this resume is the active resume.",
        examples=[True],
    )
    context: str | None = Field(
        default=None,
        description="Saved work context / last state.",
        examples=["Wiring dashboard to PostgreSQL"],
    )
    target_page: str | None = Field(
        default=None,
        max_length=200,
        description="Page to resume on.",
        examples=["/projects"],
    )


class ResumeUpdate(BaseModel):
    """Payload for updating an existing resume entry."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated resume title.",
        examples=["Senior DevOps Engineer"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated resume description.",
        examples=["10 years of IT operations experience."],
    )
    available: bool | None = Field(
        default=None,
        description="Whether this resume is the active resume.",
        examples=[True],
    )
    context: str | None = Field(
        default=None,
        description="Updated saved work context.",
    )
    target_page: str | None = Field(
        default=None,
        max_length=200,
        description="Updated page to resume on.",
    )


class ResumeResponse(BaseModel):
    """Resume returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique resume identifier.",
        examples=[1],
    )
    title: str = Field(
        ...,
        description="Resume title.",
        examples=["Senior DevOps Engineer"],
    )
    description: str | None = Field(
        ...,
        description="Resume description.",
        examples=["10 years of IT operations experience."],
    )
    available: bool = Field(
        ...,
        description="Whether the resume is available for use.",
        examples=[True],
    )
    context: str | None = Field(
        default=None,
        description="Saved work context / last state.",
        examples=["Wiring dashboard to PostgreSQL"],
    )
    target_page: str | None = Field(
        default=None,
        description="Page to resume on.",
        examples=["/projects"],
    )
    started_at: datetime | None = Field(
        default=None,
        description="When this resume context was started.",
        examples=["2026-08-21T09:00:00"],
    )
    paused_at: datetime | None = Field(
        default=None,
        description="When this resume context was paused.",
        examples=["2026-08-21T10:00:00"],
    )
    resumed_at: datetime | None = Field(
        default=None,
        description="When this resume context was resumed.",
        examples=["2026-08-21T11:00:00"],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the resume was created.",
        examples=["2026-07-08T13:00:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the resume was last updated.",
        examples=["2026-07-08T13:00:00"],
    )


class ResumeListResponse(BaseModel):
    """List of resumes."""

    count: int = Field(
        ...,
        description="Total number of resumes returned.",
        examples=[3],
    )
    items: list[ResumeResponse] = Field(
        ...,
        description="Resume records.",
    )
