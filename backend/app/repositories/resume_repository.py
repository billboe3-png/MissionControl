"""
Mission Control Resume Repository

All database access for Resume entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.resume import Resume
from app.schemas.resume import ResumeCreate
from app.schemas.resume import ResumeUpdate


class ResumeRepository:
    """Data access layer for resumes stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Resume]:
        """
        Return all resumes ordered by updated_at descending.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Resume ORM instances.
        """
        stmt = select(Resume).order_by(Resume.updated_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, resume_id: int) -> Resume | None:
        """
        Return a single resume by identifier.

        Args:
            db: Active SQLAlchemy session.
            resume_id: Primary key of the resume.

        Returns:
            Resume ORM instance, or None if not found.
        """
        stmt = select(Resume).where(Resume.id == resume_id)
        return db.scalar(stmt)

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
    def create(db: Session, resume: ResumeCreate) -> Resume:
        """
        Persist a new resume.

        If the new resume is available, deactivate all existing resumes first
        to enforce the single-active-resume business rule.

        Args:
            db: Active SQLAlchemy session.
            resume: Validated resume creation payload.

        Returns:
            The persisted Resume ORM instance.
        """
        if resume.available:
            db.query(Resume).filter(Resume.available.is_(True)).update(
                {"available": False}
            )

        entity = Resume(
            title=resume.title.strip(),
            description=resume.description,
            available=resume.available,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        resume_id: int,
        resume: ResumeUpdate,
    ) -> Resume | None:
        """
        Update an existing resume with only the supplied fields.

        If available is set to True, deactivate all other resumes first
        to enforce the single-active-resume business rule.

        Args:
            db: Active SQLAlchemy session.
            resume_id: Primary key of the resume.
            resume: Validated resume update payload.

        Returns:
            Updated Resume ORM instance, or None if not found.
        """
        entity = ResumeRepository.get_by_id(db, resume_id)
        if entity is None:
            return None

        updates = resume.model_dump(exclude_unset=True)

        if updates.get("available") is True:
            db.query(Resume).filter(
                Resume.available.is_(True),
                Resume.id != resume_id,
            ).update({"available": False})

        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, resume_id: int) -> bool:
        """
        Delete a resume by identifier.

        Args:
            db: Active SQLAlchemy session.
            resume_id: Primary key of the resume.

        Returns:
            True if deleted, False if the resume was not found.
        """
        entity = ResumeRepository.get_by_id(db, resume_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True

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
