"""
Mission Control Project Service

Business logic for the Projects dashboard section and CRUD API.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.db.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Project dashboard section and CRUD operations."""

    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self._repository = repository or ProjectRepository()

    async def get_data(self, db: Session) -> dict:
        """
        Return project count and items loaded from PostgreSQL.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Dashboard projects payload with count and serialized items.
        """
        count = self._repository.get_count(db)
        projects = self._repository.get_all(db)

        return {
            "count": count,
            "items": [self._serialize_project(project) for project in projects],
        }

    async def get_all(self, db: Session) -> ProjectListResponse:
        """Return all projects as API response models."""
        logger.info("Fetching all projects")
        projects = self._repository.get_all(db)
        items = [ProjectResponse.model_validate(project) for project in projects]
        return ProjectListResponse(count=len(items), items=items)

    async def get_by_id(self, db: Session, project_id: int) -> ProjectResponse:
        """Return a single project as an API response model."""
        logger.info("Fetching project id=%s", project_id)
        project = self._repository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return ProjectResponse.model_validate(project)

    async def create(self, db: Session, data: ProjectCreate) -> ProjectResponse:
        """Create a new project and return the API response model."""
        normalized_name = ProjectRepository.normalize_name(data.name)
        logger.info("Creating project: %s", normalized_name)

        if self._repository.get_by_name(db, normalized_name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Project already exists",
            )

        payload = data.model_copy(update={"name": data.name.strip()})
        project = self._repository.create(db, payload)
        return ProjectResponse.model_validate(project)

    async def update(
        self,
        db: Session,
        project_id: int,
        data: ProjectUpdate,
    ) -> ProjectResponse:
        """Update an existing project and return the API response model."""
        logger.info("Updating project id=%s", project_id)

        existing = self._repository.get_by_id(db, project_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if data.name is not None:
            normalized_new = ProjectRepository.normalize_name(data.name)
            normalized_existing = ProjectRepository.normalize_name(existing.name)
            if normalized_new != normalized_existing:
                duplicate = self._repository.get_by_name(db, data.name)
                if duplicate is not None and duplicate.id != project_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Project already exists",
                    )
            data = data.model_copy(update={"name": data.name.strip()})

        updated = self._repository.update(db, project_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return ProjectResponse.model_validate(updated)

    async def delete(self, db: Session, project_id: int) -> None:
        """Delete a project by identifier."""
        logger.info("Deleting project id=%s", project_id)

        deleted = self._repository.delete(db, project_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    async def close(self, db: Session, project_id: int) -> ProjectResponse:
        """Close a project by marking it inactive."""
        logger.info("Closing project id=%s", project_id)

        project = self._repository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        project.active = False
        db.commit()
        db.refresh(project)
        return ProjectResponse.model_validate(project)

    @staticmethod
    def _serialize_project(project: Project) -> dict:
        task_count = len(project.tasks)
        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": "active" if project.active else "inactive",
            "priority": None,
            "task_count": task_count,
            "note_count": len(project.notes),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }


project_service = ProjectService()
