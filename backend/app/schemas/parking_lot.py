"""
Mission Control Parking Lot API Schemas

Pydantic models for Parking Lot API endpoints.

Sprint 2.0 - Extended with backlog fields.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ParkingLotCreate(BaseModel):
    """Payload for creating a new parking lot item."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short title for the parked item.",
        examples=["Investigate Redis caching"],
    )
    description: str | None = Field(
        default=None,
        description="Detailed description of the parked item.",
        examples=["Evaluate Redis for session caching in production."],
    )
    priority: str = Field(
        default="medium",
        max_length=50,
        description="Priority level.",
        examples=["low", "medium", "high"],
    )
    status: str = Field(
        default="parked",
        max_length=50,
        description="Current status.",
        examples=["parked", "in_progress", "done"],
    )
    owner: str | None = Field(
        default=None,
        max_length=200,
        description="Person responsible for this item.",
    )
    category: str | None = Field(
        default=None,
        max_length=100,
        description="Category for grouping.",
    )
    labels: str | None = Field(
        default=None,
        description="Comma-separated labels.",
    )
    target_sprint: str | None = Field(
        default=None,
        max_length=100,
        description="Sprint this item is targeted for.",
    )
    created_by: str | None = Field(
        default=None,
        max_length=200,
        description="Person who created this item.",
    )


class ParkingLotUpdate(BaseModel):
    """Payload for updating an existing parking lot item."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated title.",
    )
    description: str | None = Field(
        default=None,
        description="Updated description.",
    )
    priority: str | None = Field(
        default=None,
        max_length=50,
        description="Updated priority level.",
    )
    status: str | None = Field(
        default=None,
        max_length=50,
        description="Updated status.",
    )
    owner: str | None = Field(
        default=None,
        max_length=200,
        description="Updated owner.",
    )
    category: str | None = Field(
        default=None,
        max_length=100,
        description="Updated category.",
    )
    labels: str | None = Field(
        default=None,
        description="Updated labels.",
    )
    target_sprint: str | None = Field(
        default=None,
        max_length=100,
        description="Updated target sprint.",
    )
    archived: bool | None = Field(
        default=None,
        description="Archive status.",
    )


class ParkingLotResponse(BaseModel):
    """Parking lot item returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique parking lot item identifier.",
    )
    title: str = Field(
        ...,
        description="Parked item title.",
    )
    description: str | None = Field(
        ...,
        description="Parked item description.",
    )
    priority: str = Field(
        ...,
        description="Priority level.",
    )
    status: str = Field(
        ...,
        description="Current status.",
    )
    owner: str | None = Field(
        default=None,
        description="Person responsible.",
    )
    category: str | None = Field(
        default=None,
        description="Category.",
    )
    labels: str | None = Field(
        default=None,
        description="Comma-separated labels.",
    )
    target_sprint: str | None = Field(
        default=None,
        description="Target sprint.",
    )
    archived: bool = Field(
        default=False,
        description="Whether this item is archived.",
    )
    created_by: str | None = Field(
        default=None,
        description="Creator.",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp.",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp.",
    )


class ParkingLotListResponse(BaseModel):
    """List of parking lot items."""

    count: int = Field(
        ...,
        description="Total number of parking lot items returned.",
    )
    items: list[ParkingLotResponse] = Field(
        ...,
        description="Parking lot item records.",
    )
