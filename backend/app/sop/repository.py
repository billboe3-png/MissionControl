"""
Mission Control SOP Document Repository
"""
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.sop_document import SOPApproval, SOPDocument
from app.schemas.sop_document import (
    SOPApprovalCreate,
    SOPDocumentCreate,
    SOPDocumentUpdate,
)


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


class SOPDocumentRepository:
    """Data access layer for SOP documents stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[SOPDocument]:
        stmt = select(SOPDocument).order_by(SOPDocument.updated_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, sop_id: int) -> SOPDocument | None:
        stmt = select(SOPDocument).where(SOPDocument.id == sop_id)
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, payload: SOPDocumentCreate) -> SOPDocument:
        entity = SOPDocument(
            title=payload.title.strip(),
            description=_normalize(payload.description),
            status=payload.status.strip().lower() if payload.status else "draft",
            approval_status=(
                payload.approval_status.strip().lower()
                if payload.approval_status
                else "pending"
            ),
            version=_normalize(payload.version),
            created_by=_normalize(payload.created_by),
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, sop_id: int, payload: SOPDocumentUpdate) -> SOPDocument | None:
        entity = SOPDocumentRepository.get_by_id(db, sop_id)
        if entity is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if field in {"title"} and value is not None:
                value = value.strip()
            if field in {"description", "version", "created_by", "approved_by"}:
                value = _normalize(value)
            if field == "status" and isinstance(value, str):
                value = value.strip().lower()
            if field == "approval_status" and isinstance(value, str):
                value = value.strip().lower()
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, sop_id: int) -> bool:
        entity = SOPDocumentRepository.get_by_id(db, sop_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def get_count(db: Session) -> int:
        stmt = select(func.count()).select_from(SOPDocument)
        return db.scalar(stmt) or 0

    @staticmethod
    def add_approval(db: Session, sop_id: int, payload: SOPApprovalCreate) -> SOPApproval | None:
        document = SOPDocumentRepository.get_by_id(db, sop_id)
        if document is None:
            return None
        entity = SOPApproval(
            sop_document_id=sop_id,
            approver_name=payload.approver_name.strip(),
            action=payload.action.strip().lower(),
            comments=_normalize(payload.comments),
            acted_at=datetime.now(UTC),
        )
        db.add(entity)
        document.approval_status = entity.action
        document.approved_by = entity.approver_name
        document.approved_at = entity.acted_at
        if document.approval_status == "approved":
            document.status = "active"
        elif document.approval_status == "rejected":
            document.status = "draft"
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def get_approvals(db: Session, sop_id: int) -> list[SOPApproval]:
        stmt = (
            select(SOPApproval)
            .where(SOPApproval.sop_document_id == sop_id)
            .order_by(SOPApproval.acted_at.desc())
        )
        return list(db.scalars(stmt).all())


def extract_text_from_file(path: str | Path) -> str | None:
    """Extract text from a PDF or Word document for search/indexing."""
    suffix = Path(path).suffix.lower()
    text: str | None = None
    try:
        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix in {".docx", ".doc"}:
            import docx
            document = docx.Document(str(path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception:
        text = None
    return text
