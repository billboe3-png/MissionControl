"""
Mission Control SOP Database Models
"""
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

if TYPE_CHECKING:
    pass


class SOPCategory(Base):
    """SOP category for organization."""

    __tablename__ = "sop_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sop_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class SOP(Base):
    """Main SOP entity representing operational knowledge."""

    __tablename__ = "sops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    site_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sop_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    approved_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    current_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    approval_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Structured SOP fields
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_tools: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedure: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation: Mapped[str | None] = mapped_column(Text, nullable=True)
    troubleshooting: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollback: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_sops: Mapped[str | None] = mapped_column(Text, nullable=True)


class SOPVersion(Base):
    """Versioned content for an SOP."""

    __tablename__ = "sop_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False, default="user_provided", index=True)

    # Structured content snapshot
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_tools: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedure: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation: Mapped[str | None] = mapped_column(Text, nullable=True)
    troubleshooting: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollback: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_sops: Mapped[str | None] = mapped_column(Text, nullable=True)

    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SOPSource(Base):
    """Metadata for ingested source documents. Does NOT store the original file."""

    __tablename__ = "sop_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sop_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sops.id", ondelete="CASCADE"), nullable=True, index=True
    )

    source_name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_author: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_pages: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_sections: Mapped[str | None] = mapped_column(Text, nullable=True)

    imported_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SOPApproval(Base):
    """Approval decision record for an SOP or SOP version."""

    __tablename__ = "sop_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sop_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sops.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sop_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sop_versions.id", ondelete="CASCADE"), nullable=True, index=True
    )

    action: Mapped[str] = mapped_column(String(20), nullable=False)
    approver_name: Mapped[str] = mapped_column(String(200), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class SOPAuditEvent(Base):
    """SOP-specific audit event."""

    __tablename__ = "sop_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sop_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sops.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sop_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sop_versions.id", ondelete="CASCADE"), nullable=True, index=True
    )

    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    site_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), index=True)
