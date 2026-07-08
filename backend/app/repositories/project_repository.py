"""
Mission Control Project Repository

All database access for Project entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.project import Project


class ProjectRepository:
    """Data access layer for projects stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Project]:
        """
        Return all projects ordered by id.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Project ORM instances.
        """
        stmt = select(Project).order_by(Project.id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_count(db: Session) -> int:
        """
        Return the total number of projects.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Project count from PostgreSQL.
        """
        stmt = select(func.count()).select_from(Project)
        return db.scalar(stmt) or 0
