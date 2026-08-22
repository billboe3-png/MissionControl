"""
Mission Control SOP Schemas
"""
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SOPStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class SOPContentType(StrEnum):
    SOURCE = "source"
    AI_GENERATED = "ai_generated"
    AI_RECOMMENDATION = "ai_recommendation"
    USER_PROVIDED = "user_provided"
    HUMAN_APPROVED = "human_approved"


class SOPSourceType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    MANUAL = "manual"
    AI = "ai"
    IMPORTED = "imported"


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    parent_id: int | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    parent_id: int | None = None
    created_at: datetime
    updated_at: datetime


class SOPSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sop_id: int | None = None
    source_name: str
    source_type: str
    source_hash: str | None = None
    source_size_bytes: int | None = None
    source_author: str | None = None
    source_version: str | None = None
    source_pages: str | None = None
    source_sections: str | None = None
    imported_by: str | None = None
    imported_at: datetime
    processing_error: str | None = None


class SOPApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sop_id: int | None = None
    sop_version_id: int | None = None
    action: str
    approver_name: str
    comments: str | None = None
    acted_at: datetime


class SOPVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sop_id: int
    version: str
    status: str
    title: str
    description: str | None = None
    content_type: str = "user_provided"
    purpose: str | None = None
    scope: str | None = None
    audience: str | None = None
    responsibilities: str | None = None
    prerequisites: str | None = None
    required_permissions: str | None = None
    required_tools: str | None = None
    procedure: str | None = None
    decision_points: str | None = None
    validation: str | None = None
    troubleshooting: str | None = None
    escalation: str | None = None
    rollback: str | None = None
    safety_requirements: str | None = None
    references: str | None = None
    related_sops: str | None = None
    change_reason: str | None = None
    created_by: str | None = None
    created_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None


class SOPCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    company_id: int | None = None
    site_id: int | None = None
    category_id: int | None = None
    owner_id: int | None = None
    tags: str | None = None
    purpose: str | None = None
    scope: str | None = None
    audience: str | None = None
    responsibilities: str | None = None
    prerequisites: str | None = None
    required_permissions: str | None = None
    required_tools: str | None = None
    procedure: str | None = None
    decision_points: str | None = None
    validation: str | None = None
    troubleshooting: str | None = None
    escalation: str | None = None
    rollback: str | None = None
    safety_requirements: str | None = None
    references: str | None = None
    related_sops: str | None = None
    content_type: str = Field(default="user_provided")
    created_by: str | None = None
    change_reason: str | None = None


class SOPUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    category_id: int | None = None
    tags: str | None = None
    purpose: str | None = None
    scope: str | None = None
    audience: str | None = None
    responsibilities: str | None = None
    prerequisites: str | None = None
    required_permissions: str | None = None
    required_tools: str | None = None
    procedure: str | None = None
    decision_points: str | None = None
    validation: str | None = None
    troubleshooting: str | None = None
    escalation: str | None = None
    rollback: str | None = None
    safety_requirements: str | None = None
    references: str | None = None
    related_sops: str | None = None
    change_reason: str | None = None


class SOPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None = None
    site_id: int | None = None
    title: str
    description: str | None = None
    category_id: int | None = None
    owner_id: int | None = None
    approved_by_id: int | None = None
    status: str
    current_version: str | None = None
    review_date: datetime | None = None
    approval_date: datetime | None = None
    published_at: datetime | None = None
    tags: str | None = None
    created_at: datetime
    updated_at: datetime
    purpose: str | None = None
    scope: str | None = None
    audience: str | None = None
    responsibilities: str | None = None
    prerequisites: str | None = None
    required_permissions: str | None = None
    required_tools: str | None = None
    procedure: str | None = None
    decision_points: str | None = None
    validation: str | None = None
    troubleshooting: str | None = None
    escalation: str | None = None
    rollback: str | None = None
    safety_requirements: str | None = None
    references: str | None = None
    related_sops: str | None = None


class SOPListResponse(BaseModel):
    count: int
    items: list[SOPResponse]


class SOPImportRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    company_id: int | None = None
    site_id: int | None = None
    category_id: int | None = None
    owner_id: int | None = None
    tags: str | None = None
    created_by: str | None = None


class SOPImportResponse(BaseModel):
    sop: SOPResponse
    source: SOPSourceResponse
    extracted_text: str | None = None
    source_deleted: bool = False


class SOPReviewResponse(BaseModel):
    assessment: str
    completeness_score: float
    risk_level: str
    findings: list[str]
    recommendations: list[str]
    evidence: list[str]
    confidence: float


class AIQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]
    confidence: dict[str, Any]
    related_data: dict[str, Any]
    suggested_actions: list[str]
