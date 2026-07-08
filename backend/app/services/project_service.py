"""
Mission Control Project Service

Business logic for the Projects dashboard section.
"""

from sqlalchemy.orm import Session

from app.models.db.project import Project
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    """Project dashboard section."""

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

    @staticmethod
    def _serialize_project(project: Project) -> dict:
        """
        Map a Project ORM instance to the dashboard item shape.

        Status is derived from the stored active flag. Priority is not
        persisted in the current schema and is returned as null.
        """
        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": "active" if project.active else "inactive",
            "priority": None,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }


project_service = ProjectService()
