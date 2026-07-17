"""
Mission Control Task Service

Business logic for the Tasks dashboard section.

Sprint:
    1.1.0B
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.db.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """Task dashboard section."""

    def __init__(self, repository: TaskRepository | None = None) -> None:
        self._repository = repository or TaskRepository()

    async def get_all(self, db: Session) -> TaskListResponse:
        """Return all tasks as API response models."""
        logger.info("Fetching all tasks")
        tasks = self._repository.get_all(db)
        items = [TaskResponse.model_validate(task) for task in tasks]
        return TaskListResponse(count=len(items), items=items)

    async def get_by_id(self, db: Session, task_id: int) -> TaskResponse:
        """Return a single task as an API response model."""
        logger.info("Fetching task id=%s", task_id)
        task = self._repository.get_by_id(db, task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return TaskResponse.model_validate(task)

    async def create(self, db: Session, data: TaskCreate) -> TaskResponse:
        """Create a new task and return the API response model."""
        logger.info("Creating task: %s", data.title)

        if ProjectRepository().get_by_id(db, data.project_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if (
            self._repository.get_by_project_and_title(
                db,
                data.project_id,
                data.title,
            )
            is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task already exists",
            )

        task = self._repository.create(db, data)
        return TaskResponse.model_validate(task)

    async def update(
        self,
        db: Session,
        task_id: int,
        data: TaskUpdate,
    ) -> TaskResponse:
        """Update an existing task and return the API response model."""
        logger.info("Updating task id=%s", task_id)

        existing = self._repository.get_by_id(db, task_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        updates = data.model_dump(exclude_unset=True)

        if "project_id" in updates:
            if ProjectRepository().get_by_id(db, updates["project_id"]) is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

        new_project_id = updates.get("project_id", existing.project_id)
        new_title = updates.get("title", existing.title)
        combination_changes = False

        if (
            "project_id" in updates
            and updates["project_id"] != existing.project_id
        ):
            combination_changes = True
        if "title" in updates and updates["title"] is not None:
            if (
                updates["title"].strip().lower()
                != existing.title.strip().lower()
            ):
                combination_changes = True

        if combination_changes:
            duplicate = self._repository.get_by_project_and_title(
                db,
                new_project_id,
                new_title,
            )
            if duplicate is not None and duplicate.id != task_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Task already exists",
                )

        if "title" in updates and updates["title"] is not None:
            data = data.model_copy(update={"title": updates["title"].strip()})

        updated = self._repository.update(db, task_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return TaskResponse.model_validate(updated)

    async def delete(self, db: Session, task_id: int) -> None:
        """Delete a task by identifier."""
        logger.info("Deleting task id=%s", task_id)

        deleted = self._repository.delete(db, task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

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
