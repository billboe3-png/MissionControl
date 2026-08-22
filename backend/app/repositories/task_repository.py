"""
Mission Control Task Repository

All database access for Task entities.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.db.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository:
    """Data access layer for tasks stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Task]:
        """
        Return all tasks ordered by creation date descending with their parent
        project loaded.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Task ORM instances.
        """
        stmt = (
            select(Task)
            .options(selectinload(Task.project))
            .order_by(Task.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Task | None:
        """
        Return a single task by identifier.

        Args:
            db: Active SQLAlchemy session.
            task_id: Primary key of the task.

        Returns:
            Task ORM instance, or None if not found.
        """
        stmt = select(Task).where(Task.id == task_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_project_and_title(
        db: Session,
        project_id: int,
        title: str,
    ) -> Task | None:
        """
        Return a task by project and title using a case-insensitive lookup.

        Args:
            db: Active SQLAlchemy session.
            project_id: Identifier of the parent project.
            title: Task title to search for.

        Returns:
            Task ORM instance, or None if not found.
        """
        normalized = title.strip().lower()
        stmt = select(Task).where(
            Task.project_id == project_id,
            func.lower(func.trim(Task.title)) == normalized,
        )
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, task: TaskCreate) -> Task:
        """
        Persist a new task.

        Args:
            db: Active SQLAlchemy session.
            task: Validated task creation payload.

        Returns:
            The persisted Task ORM instance.
        """
        entity = Task(
            project_id=task.project_id,
            title=task.title.strip(),
            description=task.description,
            status=task.status,
            priority=task.priority,
            assignee=getattr(task, "assignee", None),
            due_date=getattr(task, "due_date", None),
            started_at=datetime.now(UTC) if getattr(task, "status", None) == "in_progress" else None,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        task_id: int,
        task: TaskUpdate,
    ) -> Task | None:
        """
        Update an existing task with only the supplied fields.

        Args:
            db: Active SQLAlchemy session.
            task_id: Primary key of the task.
            task: Validated task update payload.

        Returns:
            Updated Task ORM instance, or None if not found.
        """
        entity = TaskRepository.get_by_id(db, task_id)
        if entity is None:
            return None

        updates = task.model_dump(exclude_unset=True)
        if "title" in updates and updates["title"] is not None:
            updates["title"] = updates["title"].strip()
        if updates.get("status") == "in_progress" and not entity.started_at:
            updates["started_at"] = datetime.now(UTC)
        if updates.get("status") == "completed" and not entity.completed_at:
            updates["completed_at"] = datetime.now(UTC)
        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, task_id: int) -> bool:
        """
        Delete a task by identifier.

        Args:
            db: Active SQLAlchemy session.
            task_id: Primary key of the task.

        Returns:
            True if deleted, False if the task was not found.
        """
        entity = TaskRepository.get_by_id(db, task_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def get_count(db: Session) -> int:
        """
        Return the total number of tasks.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Task count from PostgreSQL.
        """
        stmt = select(func.count()).select_from(Task)
        return db.scalar(stmt) or 0

    @staticmethod
    def create_many(db: Session, tasks: list[Task]) -> list[Task]:
        """
        Persist multiple tasks in a single transaction.

        Args:
            db: Active SQLAlchemy session.
            tasks: Task ORM instances to insert.

        Returns:
            The persisted Task ORM instances.
        """
        db.add_all(tasks)
        db.commit()
        for task in tasks:
            db.refresh(task)
        return tasks
