"""
Mission Control Task Service

Business logic for the Tasks dashboard section.

Sprint:
    1.1.0B
"""

from sqlalchemy.orm import Session

from app.models.db.task import Task
from app.repositories.task_repository import TaskRepository


class TaskService:
    """Task dashboard section."""

    def __init__(self, repository: TaskRepository | None = None) -> None:
        self._repository = repository or TaskRepository()

    async def get_data(self, db: Session) -> dict:
        """
        Return task count and items loaded from PostgreSQL.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Dashboard tasks payload with count and serialized items.
        """
        count = self._repository.get_count(db)
        tasks = self._repository.get_all(db)

        return {
            "count": count,
            "items": [self._serialize_task(task) for task in tasks],
        }

    @staticmethod
    def _serialize_task(task: Task) -> dict:
        """
        Map a Task ORM instance to the dashboard item shape.
        """
        return {
            "id": str(task.id),
            "project_id": str(task.project_id),
            "project_name": task.project.name,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }


task_service = TaskService()
