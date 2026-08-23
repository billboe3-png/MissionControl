"""
Mission Control SOP Repository
"""
import hashlib
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.db.sop import (
    SOP,
    SOPApproval,
    SOPAuditEvent,
    SOPSource,
    SOPVersion,
)
from app.schemas.sop import (
    SOPCreate,
    SOPUpdate,
)


class SOPRepository:
    @staticmethod
    def get_all(db: Session, company_id: int | None = None, site_id: int | None = None, status: str | None = None, q: str | None = None) -> list[SOP]:
        stmt = select(SOP)
        if company_id is not None:
            stmt = stmt.where(SOP.company_id == company_id)
        if site_id is not None:
            stmt = stmt.where(SOP.site_id == site_id)
        if status:
            stmt = stmt.where(SOP.status == status)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(SOP.title.ilike(like), SOP.description.ilike(like), SOP.purpose.ilike(like), SOP.procedure.ilike(like)))
        stmt = stmt.order_by(SOP.updated_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, sop_id: int) -> SOP | None:
        return db.scalar(select(SOP).where(SOP.id == sop_id))

    @staticmethod
    def create(db: Session, payload: SOPCreate) -> SOP:
        entity = SOP(
            title=payload.title.strip(),
            description=(payload.description or None),
            company_id=payload.company_id,
            site_id=payload.site_id,
            category_id=payload.category_id,
            owner_id=payload.owner_id,
            tags=(payload.tags or None),
            purpose=payload.purpose,
            scope=payload.scope,
            audience=payload.audience,
            responsibilities=payload.responsibilities,
            prerequisites=payload.prerequisites,
            required_permissions=payload.required_permissions,
            required_tools=payload.required_tools,
            procedure=payload.procedure,
            decision_points=payload.decision_points,
            validation=payload.validation,
            troubleshooting=payload.troubleshooting,
            escalation=payload.escalation,
            rollback=payload.rollback,
            safety_requirements=payload.safety_requirements,
            references=payload.references,
            related_sops=payload.related_sops,
        )
        db.add(entity)
        db.flush()
        version = SOPRepository._create_version(db, entity, payload)
        entity.current_version = version.version
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, sop_id: int, payload: SOPUpdate, actor: str | None = None, change_reason: str | None = None) -> SOP | None:
        entity = SOPRepository.get_by_id(db, sop_id)
        if entity is None:
            return None
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if value is not None:
                setattr(entity, field, value)
        if change_reason:
            version = SOPRepository._create_version(db, entity, payload, change_reason=change_reason, created_by=actor)
            entity.current_version = version.version
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, sop_id: int) -> bool:
        entity = SOPRepository.get_by_id(db, sop_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def add_source(db: Session, sop_id: int, source_name: str, source_type: str, content: str | None, file_hash: str | None = None, importing_user: str | None = None) -> SOPSource:
        entity = SOPSource(
            sop_id=sop_id,
            source_name=source_name,
            source_type=source_type,
            source_hash=file_hash,
            source_size_bytes=len(content.encode("utf-8")) if content else None,
            imported_by=importing_user,
        )
        db.add(entity)
        return entity

    @staticmethod
    def add_version(db: Session, sop: SOP, payload: SOPCreate | SOPUpdate, content_type: str = "user_provided", created_by: str | None = None, change_reason: str | None = None) -> SOPVersion:
        return SOPRepository._create_version(db, sop, payload, content_type=content_type, created_by=created_by, change_reason=change_reason)

    @staticmethod
    def _create_version(db: Session, sop: SOP, payload: SOPCreate | SOPUpdate, content_type: str = "user_provided", created_by: str | None = None, change_reason: str | None = None) -> SOPVersion:
        versions = list(db.scalars(select(SOPVersion).where(SOPVersion.sop_id == sop.id).order_by(SOPVersion.id.desc())).all()[:20])
        next_version = "1.0"
        if versions:
            try:
                major, minor = versions[0].version.split(".", 1)
                next_version = f"{major}.{int(minor) + 1}"
            except Exception:
                next_version = versions[0].version
        data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.__dict__
        structured_fields = [
            "title", "description", "purpose", "scope", "audience", "responsibilities",
            "prerequisites", "required_permissions", "required_tools", "procedure",
            "decision_points", "validation", "troubleshooting", "escalation", "rollback",
            "safety_requirements", "references", "related_sops",
        ]
        version = SOPVersion(
            sop_id=sop.id,
            version=next_version,
            status=sop.status if sop else "draft",
            content_type=content_type,
            change_reason=change_reason,
            created_by=created_by,
            **{field: sop.__dict__.get(field) if isinstance(payload, SOPUpdate) else data.get(field) for field in structured_fields},
        )
        db.add(version)
        db.flush()
        return version

    @staticmethod
    def add_approval(db: Session, sop_id: int | None, sop_version_id: int | None, action: str, approver_name: str, comments: str | None = None) -> SOPApproval | None:
        entity = SOPApproval(sop_id=sop_id, sop_version_id=sop_version_id, action=action.strip().lower(), approver_name=approver_name.strip(), comments=comments)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def audit(db: Session, action: str, sop_id: int | None = None, sop_version_id: int | None = None, actor: str | None = None, details: str | None = None, source: str | None = None, company_id: int | None = None, site_id: int | None = None) -> SOPAuditEvent:
        entity = SOPAuditEvent(action=action, actor=actor, details=details, source=source, sop_id=sop_id, sop_version_id=sop_version_id, company_id=company_id, site_id=site_id)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity


class SOPSearchRepository:
    @staticmethod
    def search(db: Session, q: str, company_id: int | None = None, limit: int = 25) -> list[SOP]:
        like = f"%{q}%"
        stmt = (
            select(SOP)
            .where(
                or_(
                    SOP.title.ilike(like),
                    SOP.description.ilike(like),
                    SOP.purpose.ilike(like),
                    SOP.procedure.ilike(like),
                    SOP.tags.ilike(like),
                    SOP.references.ilike(like),
                )
            )
            .order_by(SOP.updated_at.desc())
            .limit(limit)
        )
        if company_id is not None:
            stmt = stmt.where(SOP.company_id == company_id)
        return list(db.scalars(stmt).all())


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    if suffix == ".docx":
        try:
            import docx
            document = docx.Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
        except Exception:
            return ""
    try:
        return path.read_text(errors="ignore")
    except Exception:
        return ""
