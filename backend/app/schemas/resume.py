"""
Mission Control Resume API Schemas

Pydantic models for Resume API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ResumeCreate(BaseModel):
    """Payload for creating a new resume."""

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


class ResumeUpdate(BaseModel):
    """Payload for updating an existing resume."""

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
