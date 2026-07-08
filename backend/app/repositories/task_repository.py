"""
Mission Control Task Repository

All database access for Task entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.db.task import Task


class TaskRepository:
    """Data access layer for tasks stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Task]:
        """
        Return all tasks ordered by id with their parent project loaded.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Task ORM instances.
        """
        stmt = (
            select(Task)
            .options(selectinload(Task.project))
            .order_by(Task.id)
        )
        return list(db.scalars(stmt).all())

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
