"""
Mission Control Resume Repository

All database access for Resume entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.resume import Resume


class ResumeRepository:
    """Data access layer for resumes stored in PostgreSQL."""

    @staticmethod
    def get_active(db: Session) -> Resume | None:
        """
        Return the most recently updated available resume.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Active Resume ORM instance or None.
        """
        stmt = (
            select(Resume)
            .where(Resume.available.is_(True))
            .order_by(Resume.updated_at.desc())
            .limit(1)
        )
        return db.scalar(stmt)

    @staticmethod
    def get_count(db: Session) -> int:
        """
        Return the total number of resumes.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Resume count from PostgreSQL.
        """
        stmt = select(func.count()).select_from(Resume)
        return db.scalar(stmt) or 0

    @staticmethod
    def create_many(db: Session, resumes: list[Resume]) -> list[Resume]:
        """
        Persist multiple resumes in a single transaction.

        Args:
            db: Active SQLAlchemy session.
            resumes: Resume ORM instances to insert.

        Returns:
            The persisted Resume ORM instances.
        """
        db.add_all(resumes)
        db.commit()
        for resume in resumes:
            db.refresh(resume)
        return resumes
