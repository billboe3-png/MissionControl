"""
Mission Control Audit Trail API Schemas

Sprint 2.8 - Automation & Playbooks.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AuditTrailResponse(BaseModel):
    """Response for a single audit trail entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int | None
    action: str
    actor: str | None
    details: str | None
    ip_address: str | None
    timestamp: datetime


class AuditTrailListResponse(BaseModel):
    """Response for listing audit trail entries."""

    count: int
    items: list[AuditTrailResponse]


class AuditTrailCreateRequest(BaseModel):
    """Internal payload for creating audit trail entries."""

    entity_type: str = Field(..., max_length=50)
    entity_id: int | None = None
    action: str = Field(..., max_length=50)
    actor: str | None = Field(default=None, max_length=200)
    details: str | None = Field(default=None)
    ip_address: str | None = Field(default=None, max_length=50)
