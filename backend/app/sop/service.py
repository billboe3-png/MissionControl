"""
Mission Control SOP Service
"""
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.events import Event, EventType, event_bus
from app.models.db.sop import SOPSource, SOPVersion
from app.schemas.sop import (
    AIQueryResponse,
    SOPCreate,
    SOPImportResponse,
    SOPListResponse,
    SOPResponse,
    SOPReviewResponse,
    SOPUpdate,
    SOPVersionResponse,
    SOPSourceResponse,
)
from app.sop.ai_helpers import ai_query_sops, ai_review_sop
from app.sop.repository import (
    SOPRepository,
    SOPSearchRepository,
    compute_sha256,
    extract_text_from_file,
)

logger = logging.getLogger(__name__)


class SOPService:
    def __init__(self, repository: SOPRepository | None = None) -> None:
        self._repository = repository or SOPRepository()

    async def list_sops(self, db: Session, company_id: int | None, site_id: int | None, status: str | None, q: str | None) -> SOPListResponse:
        items = self._repository.get_all(db, company_id=company_id, site_id=site_id, status=status, q=q)
        return SOPListResponse(count=len(items), items=[SOPResponse.model_validate(item) for item in items])

    async def get_sop(self, db: Session, sop_id: int) -> SOPResponse:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        return SOPResponse.model_validate(entity)

    async def create_sop(self, db: Session, payload: SOPCreate, actor: str | None = None) -> SOPResponse:
        entity = self._repository.create(db, payload)
        SOPRepository.audit(db, action="sop.created", sop_id=entity.id, actor=actor, source="api")
        await event_bus.publish(Event(type=EventType.SOP_CREATED, source="backend", data={"sop_id": entity.id, "title": entity.title, "actor": actor}))
        return SOPResponse.model_validate(entity)

    async def update_sop(self, db: Session, sop_id: int, payload: SOPUpdate, actor: str | None = None, change_reason: str | None = None) -> SOPResponse:
        entity = self._repository.update(db, sop_id, payload, actor=actor, change_reason=change_reason)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        SOPRepository.audit(db, action="sop.updated", sop_id=entity.id, actor=actor, details=change_reason, source="api")
        await event_bus.publish(Event(type=EventType.SOP_UPDATED, source="backend", data={"sop_id": entity.id, "title": entity.title, "actor": actor}))
        return SOPResponse.model_validate(entity)

    async def delete_sop(self, db: Session, sop_id: int, actor: str | None = None) -> None:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        SOPRepository.audit(db, action="sop.deleted", sop_id=sop_id, actor=actor, source="api")
        self._repository.delete(db, sop_id)
        await event_bus.publish(Event(type=EventType.SOP_ARCHIVED, source="backend", data={"sop_id": sop_id, "actor": actor}))

    async def submit_sop(self, db: Session, sop_id: int, actor: str | None = None) -> SOPResponse:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        entity.status = "pending_approval"
        db.commit()
        db.refresh(entity)
        SOPRepository.audit(db, action="sop.submitted", sop_id=sop_id, actor=actor, source="api")
        await event_bus.publish(Event(type=EventType.SOP_SUBMITTED, source="backend", data={"sop_id": sop_id, "actor": actor}))
        return SOPResponse.model_validate(entity)

    async def approve_sop(self, db: Session, sop_id: int, approver_name: str, comments: str | None = None) -> SOPResponse:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        entity.status = "approved"
        entity.approved_by_id = None
        entity.approval_date = datetime.now(UTC)
        self._repository.add_approval(db, sop_id=sop_id, sop_version_id=None, action="approved", approver_name=approver_name, comments=comments)
        db.commit()
        db.refresh(entity)
        SOPRepository.audit(db, action="sop.approved", sop_id=sop_id, actor=approver_name, source="api")
        await event_bus.publish(Event(type=EventType.SOP_APPROVED, source="backend", data={"sop_id": sop_id, "actor": approver_name}))
        return SOPResponse.model_validate(entity)

    async def reject_sop(self, db: Session, sop_id: int, approver_name: str, comments: str | None = None) -> SOPResponse:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        entity.status = "rejected"
        self._repository.add_approval(db, sop_id=sop_id, sop_version_id=None, action="rejected", approver_name=approver_name, comments=comments)
        db.commit()
        db.refresh(entity)
        SOPRepository.audit(db, action="sop.rejected", sop_id=sop_id, actor=approver_name, details=comments, source="api")
        await event_bus.publish(Event(type=EventType.SOP_REJECTED, source="backend", data={"sop_id": sop_id, "actor": approver_name}))
        return SOPResponse.model_validate(entity)

    async def publish_sop(self, db: Session, sop_id: int, actor: str | None = None) -> SOPResponse:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        entity.status = "published"
        entity.published_at = datetime.now(UTC)
        db.commit()
        db.refresh(entity)
        SOPRepository.audit(db, action="sop.published", sop_id=sop_id, actor=actor, source="api")
        await event_bus.publish(Event(type=EventType.SOP_PUBLISHED, source="backend", data={"sop_id": sop_id, "actor": actor}))
        return SOPResponse.model_validate(entity)

    async def get_versions(self, db: Session, sop_id: int) -> list[SOPVersionResponse]:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        versions = list(db.scalars(select(SOPVersion).where(SOPVersion.sop_id == sop_id).order_by(SOPVersion.created_at.desc())).all())
        return [SOPVersionResponse.model_validate(v) for v in versions]

    async def search(self, db: Session, q: str, company_id: int | None = None) -> SOPListResponse:
        items = SOPSearchRepository.search(db, q, company_id=company_id)
        return SOPListResponse(count=len(items), items=[SOPResponse.model_validate(item) for item in items])

    async def import_document(self, db: Session, file_path: Path, source_name: str, payload: Any, importing_user: str | None = None) -> SOPImportResponse:
        text = extract_text_from_file(file_path)
        source_type = source_name.rsplit(".", 1)[-1].lower() if "." in source_name else "unknown"
        file_hash = compute_sha256(file_path)
        existing = db.scalars(select(SOPSource).where(SOPSource.source_hash == file_hash).limit(1)).first()
        if existing and existing.sop_id:
            existing_sop = self._repository.get_by_id(db, existing.sop_id)
            if existing_sop:
                return SOPImportResponse(sop=SOPResponse.model_validate(existing_sop), source=SOPSourceResponse.model_validate(existing), extracted_text=text, source_deleted=True)
        create_payload = SOPCreate(
            title=payload.title,
            description=payload.description,
            company_id=payload.company_id,
            site_id=payload.site_id,
            category_id=payload.category_id,
            owner_id=payload.owner_id,
            tags=payload.tags,
            created_by=importing_user,
        )
        sop = self._repository.create(db, create_payload)
        source = self._repository.add_source(db, sop.id, source_name=source_name, source_type=source_type, content=text, file_hash=file_hash, importing_user=importing_user)
        db.commit()
        db.refresh(source)
        SOPRepository.audit(db, action="sop.imported", sop_id=sop.id, actor=importing_user, details=source_name, source="ingestion")
        await event_bus.publish(Event(type=EventType.SOP_IMPORTED, source="backend", data={"sop_id": sop.id, "source": source_name, "hash": file_hash}))
        return SOPImportResponse(sop=SOPResponse.model_validate(sop), source=SOPSourceResponse.model_validate(source), extracted_text=text, source_deleted=True)

    async def ai_review(self, db: Session, sop_id: int) -> SOPReviewResponse:
        entity = self._repository.get_by_id(db, sop_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP not found")
        data = await ai_review_sop(entity)
        return SOPReviewResponse(**data)

    async def ai_query(self, db: Session, question: str, company_id: int | None = None) -> AIQueryResponse:
        items = SOPSearchRepository.search(db, question, company_id=company_id)
        approved = [item for item in items if item.status == "published"]
        data = await ai_query_sops(approved, question)
        return AIQueryResponse(
            query=question,
            answer=data["answer"],
            sources=data["sources"],
            confidence={"score": data["confidence_score"]},
            related_data={},
            suggested_actions=[],
        )


sop_service = SOPService()
