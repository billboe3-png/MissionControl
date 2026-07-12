"""
Mission Control Resume Service

Business logic for the Resume dashboard section.

Sprint:
    1.1.0E
"""

import logging

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeCreate
from app.schemas.resume import ResumeListResponse
from app.schemas.resume import ResumeResponse
from app.schemas.resume import ResumeUpdate

logger = logging.getLogger(__name__)


class ResumeService:
    """Resume previous work."""

    def __init__(self, repository: ResumeRepository | None = None) -> None:
        self._repository = repository or ResumeRepository()

    async def get_all(self, db: Session) -> ResumeListResponse:
        """Return all resumes as API response models."""
        logger.info("Fetching resumes")
        resumes = self._repository.get_all(db)
        items = [ResumeResponse.model_validate(r) for r in resumes]
        return ResumeListResponse(count=len(items), items=items)

    async def get_by_id(self, db: Session, resume_id: int) -> ResumeResponse:
        """Return a single resume as an API response model."""
        logger.info("Fetching resume id=%s", resume_id)
        resume = self._repository.get_by_id(db, resume_id)
        if resume is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )
        return ResumeResponse.model_validate(resume)

    async def create(self, db: Session, data: ResumeCreate) -> ResumeResponse:
        """Create a new resume and return the API response model."""
        logger.info("Creating resume: %s", data.title)
        resume = self._repository.create(db, data)
        return ResumeResponse.model_validate(resume)

    async def update(
        self,
        db: Session,
        resume_id: int,
        data: ResumeUpdate,
    ) -> ResumeResponse:
        """Update an existing resume and return the API response model."""
        logger.info("Updating resume id=%s", resume_id)
        updated = self._repository.update(db, resume_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )
        return ResumeResponse.model_validate(updated)

    async def delete(self, db: Session, resume_id: int) -> None:
        """Delete a resume by identifier."""
        logger.info("Deleting resume id=%s", resume_id)
        deleted = self._repository.delete(db, resume_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )

    async def get_data(self, db: Session) -> dict:
        """
        Return the active resume context from PostgreSQL.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Dashboard resume payload.
        """
        resume = self._repository.get_active(db)
        if resume is None:
            return {
                "available": False,
                "title": None,
                "description": None,
            }

        return {
            "available": resume.available,
            "title": resume.title,
            "description": resume.description,
        }


resume_service = ResumeService()
