"""
Mission Control SOP Router
"""
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.models.db.user import User
from app.schemas.sop import (
    AIQueryResponse,
    SOPCreate,
    SOPImportRequest,
    SOPImportResponse,
    SOPListResponse,
    SOPResponse,
    SOPReviewResponse,
    SOPUpdate,
    SOPVersionResponse,
)
from app.sop.service import SOPService, sop_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sops",
    tags=["SOP"],
    dependencies=[Depends(get_current_user)],
)


def get_sop_service() -> SOPService:
    return sop_service


@router.get("", response_model=SOPListResponse, summary="List SOPs")
async def list_sops(
    company_id: int | None = None,
    site_id: int | None = None,
    category_id: int | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPListResponse:
    return await service.list_sops(
        db,
        company_id=company_id,
        site_id=site_id,
        category_id=category_id,
        status_filter=status_filter,
    )


@router.get("/search", response_model=SOPListResponse, summary="Search SOPs")
async def search_sops(
    q: str,
    company_id: int | None = None,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPListResponse:
    return await service.search(db, q, company_id=company_id)


@router.post("/import", response_model=SOPImportResponse, summary="Import temporary document into SOP")
async def import_document(
    payload: SOPImportRequest,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPImportResponse:
    return await service.import_document(
        db,
        Path(payload.file_path),
        source_name=payload.source_name,
        payload=payload,
        importing_user=current_user.email,
    )


@router.post("/query", response_model=AIQueryResponse, summary="Query approved SOPs via AI")
async def ai_query(
    query: str,
    company_id: int | None = None,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> AIQueryResponse:
    return await service.ai_query(db, query, company_id=company_id)


@router.get("/{sop_id}", response_model=SOPResponse, summary="Get SOP")
async def get_sop(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPResponse:
    return await service.get_sop(db, sop_id)


@router.post("", response_model=SOPResponse, status_code=status.HTTP_201_CREATED, summary="Create SOP")
async def create_sop(
    payload: SOPCreate,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPResponse:
    return await service.create_sop(db, payload, actor=current_user.email)


@router.put("/{sop_id}", response_model=SOPResponse, summary="Update SOP")
async def update_sop(
    sop_id: int,
    payload: SOPUpdate,
    change_reason: str | None = None,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPResponse:
    return await service.update_sop(db, sop_id, payload, actor=current_user.email, change_reason=change_reason)


@router.delete("/{sop_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete SOP")
async def delete_sop(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> None:
    await service.delete_sop(db, sop_id, actor=current_user.email)


@router.post("/{sop_id}/submit", response_model=SOPResponse, summary="Submit SOP for approval")
async def submit_sop(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPResponse:
    return await service.submit_sop(db, sop_id, actor=current_user.email)


@router.post("/{sop_id}/approve", response_model=SOPResponse, summary="Approve SOP")
async def approve_sop(
    sop_id: int,
    comments: str | None = None,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPResponse:
    return await service.approve_sop(db, sop_id, approver_name=current_user.email, comments=comments)


@router.post("/{sop_id}/reject", response_model=SOPResponse, summary="Reject SOP")
async def reject_sop(
    sop_id: int,
    comments: str | None = None,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPResponse:
    return await service.reject_sop(db, sop_id, approver_name=current_user.email, comments=comments)


@router.post("/{sop_id}/publish", response_model=SOPResponse, summary="Publish SOP")
async def publish_sop(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
    current_user: User = Depends(get_current_user),
) -> SOPResponse:
    return await service.publish_sop(db, sop_id, actor=current_user.email)


@router.get("/{sop_id}/versions", response_model=list[SOPVersionResponse], summary="List SOP versions")
async def list_versions(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> list[SOPVersionResponse]:
    return await service.get_versions(db, sop_id)


@router.post("/{sop_id}/ai/review", response_model=SOPReviewResponse, summary="AI review SOP")
async def ai_review(
    sop_id: int,
    db: Session = Depends(get_db),
    service: SOPService = Depends(get_sop_service),
) -> SOPReviewResponse:
    return await service.ai_review(db, sop_id)
