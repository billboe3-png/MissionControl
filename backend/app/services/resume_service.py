"""
Mission Control Resume Service

Business logic for the Resume dashboard section.

Sprint:
    1.1.0E
"""

from sqlalchemy.orm import Session

from app.repositories.resume_repository import ResumeRepository


class ResumeService:
    """Resume previous work."""

    def __init__(self, repository: ResumeRepository | None = None) -> None:
        self._repository = repository or ResumeRepository()

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
