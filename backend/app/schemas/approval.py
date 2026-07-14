"""
Mission Control Approval API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ApprovalWorkflowCreate(BaseModel):
    """Payload for creating an approval workflow."""

    name: str = Field(..., min_length=1, max_length=200)
    required_approvers: int = Field(default=1, ge=1)
    approver_roles: str | None = Field(default=None, max_length=500)
    auto_approve_on_timeout: bool = Field(default=False)
    timeout_minutes: int = Field(default=60, ge=1)
    enabled: bool = Field(default=True)


class ApprovalWorkflowUpdate(BaseModel):
    """Payload for updating an approval workflow."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    required_approvers: int | None = Field(default=None, ge=1)
    approver_roles: str | None = Field(default=None, max_length=500)
    auto_approve_on_timeout: bool | None = None
    timeout_minutes: int | None = Field(default=None, ge=1)
    enabled: bool | None = None


class ApprovalWorkflowResponse(BaseModel):
    """Response for a single approval workflow."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    name: str
    required_approvers: int
    approver_roles: str | None
    auto_approve_on_timeout: bool
    timeout_minutes: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ApprovalWorkflowListResponse(BaseModel):
    """Response for listing approval workflows."""

    count: int
    items: list[ApprovalWorkflowResponse]


class ApprovalRequestCreate(BaseModel):
    """Payload for creating an approval request."""

    execution_id: int
    workflow_id: int
    requested_by: str | None = Field(default=None, max_length=200)


class ApprovalAction(BaseModel):
    """Payload for approving/rejecting a request."""

    approved_by: str = Field(..., min_length=1, max_length=200)
    comments: str | None = Field(default=None, max_length=1000)


class ApprovalRequestResponse(BaseModel):
    """Response for a single approval request."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: int
    workflow_id: int
    status: str
    requested_by: str | None
    approved_by: str | None
    comments: str | None
    requested_at: datetime
    responded_at: datetime | None


class ApprovalRequestListResponse(BaseModel):
    """Response for listing approval requests."""

    count: int
    items: list[ApprovalRequestResponse]
