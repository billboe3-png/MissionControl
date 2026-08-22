"""
Mission Control SOP Service
"""
import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.sop_document import (
    SOPApprovalCreate,
    SOPDocumentCreate,
    SOPDocumentListResponse,
    SOPDocumentResponse,
    SOPDocumentUpdate,
)
from app.sop.repository import SOPDocumentRepository, extract_text_from_file

logger = logging.getLogger(__name__)


class SOPService:
    """Business logic for SOP documents."""

    def __init__(self, repository: SOPDocumentRepository | None = None) -> None:
        self._repository = repository or SOPDocumentRepository()

    async def list_documents(self, db: Session) -> SOPDocumentListResponse:
        logger.info("Listing SOP documents")
        documents = self._repository.get_all(db)
        items = [SOPDocumentResponse.model_validate(document) for document in documents]
        return SOPDocumentListResponse(count=len(items), items=items)

    async def get_document(self, db: Session, sop_id: int) -> SOPDocumentResponse:
        logger.info("Fetching SOP id=%s", sop_id)
        document = self._repository.get_by_id(db, sop_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP document not found",
            )
        return SOPDocumentResponse.model_validate(document)

    async def create_document(self, db: Session, payload: SOPDocumentCreate) -> SOPDocumentResponse:
        logger.info("Creating SOP: %s", payload.title)
        document = self._repository.create(db, payload)
        return SOPDocumentResponse.model_validate(document)

    async def update_document(
        self, db: Session, sop_id: int, payload: SOPDocumentUpdate
    ) -> SOPDocumentResponse:
        logger.info("Updating SOP id=%s", sop_id)
        document = self._repository.update(db, sop_id, payload)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP document not found",
            )
        return SOPDocumentResponse.model_validate(document)

    async def delete_document(self, db: Session, sop_id: int) -> None:
        logger.info("Deleting SOP id=%s", sop_id)
        deleted = self._repository.delete(db, sop_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP document not found",
            )

    async def approve_document(
        self, db: Session, sop_id: int, payload: SOPApprovalCreate
    ) -> SOPDocumentResponse:
        logger.info("Approving SOP id=%s by %s", sop_id, payload.approver_name)
        document = self._repository.get_by_id(db, sop_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP document not found",
            )
        approval = self._repository.add_approval(db, sop_id, payload)
        if approval is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP document not found",
            )
        db.refresh(document)
        return SOPDocumentResponse.model_validate(document)

    async def extract_text(self, db: Session, sop_id: int) -> dict[str, Any]:
        document = self._repository.get_by_id(db, sop_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP document not found",
            )
        if not document.file_path:
            return {"text": document.content_text, "source": "stored"}
        text = extract_text_from_file(document.file_path)
        if text is not None:
            document.content_text = text
            db.commit()
            db.refresh(document)
        return {"text": text, "source": "file" if text is not None else "stored"}


sop_service = SOPService()
