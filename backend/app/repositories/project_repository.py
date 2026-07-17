"""
Mission Control Project Repository

All database access for Project entities.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:
    """Data access layer for projects stored in PostgreSQL."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a project name for case-insensitive, trimmed comparison."""
        return name.strip().lower()

    @staticmethod
    def get_all(db: Session) -> list[Project]:
        """
        Return all projects ordered by creation date descending.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Project ORM instances.
        """
        stmt = select(Project).order_by(Project.created_at.desc())
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

    @staticmethod
    def create_many(db: Session, projects: list[Project]) -> list[Project]:
        """
        Persist multiple projects in a single transaction.

        Args:
            db: Active SQLAlchemy session.
            projects: Project ORM instances to insert.

        Returns:
            The persisted Project ORM instances.
        """
        db.add_all(projects)
        db.commit()
        for project in projects:
            db.refresh(project)
        return projects

    @staticmethod
    def get_by_id(db: Session, project_id: int) -> Project | None:
        """
        Return a single project by identifier.

        Args:
            db: Active SQLAlchemy session.
            project_id: Primary key of the project.

        Returns:
            Project ORM instance, or None if not found.
        """
        stmt = select(Project).where(Project.id == project_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Project | None:
        """
        Return a project by name using a case-insensitive, trimmed lookup.

        Args:
            db: Active SQLAlchemy session.
            name: Project name to search for.

        Returns:
            Project ORM instance, or None if not found.
        """
        normalized = ProjectRepository.normalize_name(name)
        stmt = select(Project).where(
            func.lower(func.trim(Project.name)) == normalized,
        )
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, project: ProjectCreate) -> Project:
        """
        Persist a new project.

        Args:
            db: Active SQLAlchemy session.
            project: Validated project creation payload.

        Returns:
            The persisted Project ORM instance.
        """
        entity = Project(
            name=project.name.strip(),
            description=project.description,
            active=project.active,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        project_id: int,
        project: ProjectUpdate,
    ) -> Project | None:
        """
        Update an existing project with only the supplied fields.

        Args:
            db: Active SQLAlchemy session.
            project_id: Primary key of the project.
            project: Validated project update payload.

        Returns:
            Updated Project ORM instance, or None if not found.
        """
        entity = ProjectRepository.get_by_id(db, project_id)
        if entity is None:
            return None

        updates = project.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, project_id: int) -> bool:
        """
        Delete a project by identifier.

        Args:
            db: Active SQLAlchemy session.
            project_id: Primary key of the project.

        Returns:
            True if deleted, False if the project was not found.
        """
        entity = ProjectRepository.get_by_id(db, project_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True
