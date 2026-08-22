"""
Mission Control SOP Router
"""
import logging

from app.services.sop_service import SOPService, sop_service
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.sop_document import (
    SOPApprovalCreate,
    SOPDocumentCreate,
    SOPDocumentListResponse,
    SOPDocumentResponse,
    SOPDocumentUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sop",
    tags=["SOP"],
    dependencies=[Depends(get_current_user)],
)


def get_sop_service() -> SOPService:
    """Provide the shared SOP service instance."""
    return sop_service


@router.get(
    "",
    response_model=SOPDocumentListResponse,
    summary="List SOP documents",
    description="Return all SOP documents.",
)
async def list_sops(
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPDocumentListResponse:
    return await service.list_documents(db)


@router.get(
    "/{sop_id}",
    response_model=SOPDocumentResponse,
    summary="Get SOP document",
    description="Return a single SOP document by identifier.",
)
async def get_sop(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPDocumentResponse:
    return await service.get_document(db, sop_id)


@router.post(
    "",
    response_model=SOPDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create SOP document",
    description="Create a new SOP document record.",
)
async def create_sop(
    payload: SOPDocumentCreate,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPDocumentResponse:
    return await service.create_document(db, payload)


@router.put(
    "/{sop_id}",
    response_model=SOPDocumentResponse,
    summary="Update SOP document",
    description="Replace fields on an existing SOP document.",
)
async def update_sop(
    sop_id: int,
    payload: SOPDocumentUpdate,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPDocumentResponse:
    return await service.update_document(db, sop_id, payload)


@router.delete(
    "/{sop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete SOP document",
    description="Remove an SOP document by its identifier.",
)
async def delete_sop(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> None:
    await service.delete_document(db, sop_id)


@router.post(
    "/{sop_id}/approvals",
    response_model=SOPDocumentResponse,
    summary="Approve or reject SOP document",
    description="Record an approval decision for an SOP document.",
)
async def approve_sop(
    sop_id: int,
    payload: SOPApprovalCreate,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPDocumentResponse:
    return await service.approve_document(db, sop_id, payload)
