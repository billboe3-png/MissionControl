"""
Mission Control SOP API Schemas
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SOPDocumentCreate(BaseModel):
    """Payload for creating a new SOP document."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="SOP document title.",
        examples=["Firewall change control SOP"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Short description of the SOP.",
        examples=["Standard process for firewall changes."],
    )
    status: str = Field(
        default="draft",
        max_length=20,
        description="Document status.",
        examples=["draft", "active", "archived"],
    )
    approval_status: str = Field(
        default="pending",
        max_length=20,
        description="Approval workflow status.",
        examples=["pending", "approved", "rejected"],
    )
    version: str | None = Field(
        default=None,
        max_length=50,
        description="Document version.",
        examples=["1.0"],
    )
    created_by: str | None = Field(
        default=None,
        max_length=200,
        description="Name or user ID of the author.",
        examples=["Robert Barnes"],
    )


class SOPDocumentUpdate(BaseModel):
    """Payload for updating an existing SOP document."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Updated SOP title.",
        examples=["Updated firewall SOP"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated description.",
    )
    status: str | None = Field(
        default=None,
        max_length=20,
        description="Updated document status.",
    )
    approval_status: str | None = Field(
        default=None,
        max_length=20,
        description="Updated approval status.",
    )
    version: str | None = Field(
        default=None,
        max_length=50,
        description="Updated version.",
    )
    content_text: str | None = Field(
        default=None,
        description="Replaced extracted text content for the SOP.",
    )
    approved_by: str | None = Field(
        default=None,
        max_length=200,
        description="Approver name or ID.",
    )
    approved_at: datetime | None = Field(
        default=None,
        description="Timestamp when the SOP was approved.",
    )


class SOPApprovalCreate(BaseModel):
    """Payload for recording an SOP approval decision."""

    approver_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name or user ID of the approver.",
        examples=["Robert Barnes"],
    )
    action: str = Field(
        ...,
        max_length=20,
        description="Approval action taken.",
        examples=["approved", "rejected"],
    )
    comments: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional comments.",
    )


class SOPApprovalResponse(BaseModel):
    """Approval record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(...)
    sop_document_id: int = Field(...)
    approver_name: str = Field(...)
    action: str = Field(...)
    comments: str | None = Field(default=None)
    acted_at: datetime = Field(...)


class SOPDocumentResponse(BaseModel):
    """SOP document returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(...)
    title: str = Field(...)
    description: str | None = Field(default=None)
    file_path: str | None = Field(default=None)
    content_text: str | None = Field(default=None)
    status: str = Field(...)
    approval_status: str = Field(...)
    version: str | None = Field(default=None)
    created_by: str | None = Field(default=None)
    approved_by: str | None = Field(default=None)
    approved_at: datetime | None = Field(default=None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)


class SOPDocumentListResponse(BaseModel):
    """List of SOP documents."""

    count: int = Field(...)
    items: list[SOPDocumentResponse] = Field(...)
