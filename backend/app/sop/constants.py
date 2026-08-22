"""
Mission Control SOP constants
"""
from enum import StrEnum


class SOPStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class SOPSourceType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    MANUAL = "manual"
    AI = "ai"
    IMPORTED = "imported"


class SOPContentType(StrEnum):
    SOURCE = "source"
    AI_GENERATED = "ai_generated"
    AI_RECOMMENDATION = "ai_recommendation"
    USER_PROVIDED = "user_provided"
    HUMAN_APPROVED = "human_approved"


SOP_ROLES = {
    "view": ["admin", "editor", "reviewer", "approver", "readonly"],
    "create": ["admin", "editor"],
    "edit": ["admin", "editor"],
    "review": ["admin", "reviewer"],
    "approve": ["admin", "approver"],
    "publish": ["admin", "approver"],
    "admin": ["admin"],
}


def has_sop_permission(role: str, permission: str) -> bool:
    allowed = SOP_ROLES.get(permission, [])
    return role in allowed
