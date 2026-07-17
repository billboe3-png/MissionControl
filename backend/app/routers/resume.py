"""
Mission Control Resume Router

Sprint:
    1.5.1 - Resume API GET Operations
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.resume import (
    ResumeCreate,
    ResumeListResponse,
    ResumeResponse,
    ResumeUpdate,
)
from app.services.resume_service import ResumeService, resume_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/resume",
    tags=["Resume"],
    dependencies=[Depends(get_current_user)],
)


def get_resume_service() -> ResumeService:
    """Provide the shared resume service instance."""
    return resume_service


@router.get(
    "",
    summary="List resumes",
    description="Return all resumes managed by Mission Control.",
    response_model=ResumeListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Resumes retrieved successfully.",
            "model": ResumeListResponse,
        },
    },
)
async def list_resumes(
    db: Session = Depends(get_db),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeListResponse:
    return await service.get_all(db)


@router.get(
    "/{resume_id}",
    summary="Get resume",
    description="Return a single resume by its identifier.",
    response_model=ResumeResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Resume retrieved successfully.",
            "model": ResumeResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Resume not found.",
        },
    },
)
async def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    return await service.get_by_id(db, resume_id)


@router.post(
    "",
    summary="Create resume",
    description="Create a new resume record.",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Resume created successfully.",
            "model": ResumeResponse,
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    return await service.create(db, payload)


@router.put(
    "/{resume_id}",
    summary="Update resume",
    description="Update an existing resume.",
    response_model=ResumeResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Resume updated successfully.",
            "model": ResumeResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Resume not found.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    return await service.update(db, resume_id, payload)


@router.delete(
    "/{resume_id}",
    summary="Delete resume",
    description="Delete a resume by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Resume deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Resume not found.",
        },
    },
)
async def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    service: ResumeService = Depends(get_resume_service),
) -> None:
    await service.delete(db, resume_id)
