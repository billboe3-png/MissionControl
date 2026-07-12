"""
Mission Control Dashboard Repository

Centralised read-only counts for the dashboard summary.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.note import Note
from app.models.db.project import Project
from app.models.db.resume import Resume
from app.models.db.task import Task


class DashboardRepository:
    """Aggregate statistics used by the dashboard service."""

    @staticmethod
    def count_projects(db: Session) -> int:
        """Return the total number of projects."""
        stmt = select(func.count()).select_from(Project)
        return db.scalar(stmt) or 0

    @staticmethod
    def count_active_projects(db: Session) -> int:
        """Return the number of active projects."""
        stmt = select(func.count()).select_from(Project).where(Project.active.is_(True))
        return db.scalar(stmt) or 0

    @staticmethod
    def count_tasks(db: Session) -> int:
        """Return the total number of tasks."""
        stmt = select(func.count()).select_from(Task)
        return db.scalar(stmt) or 0

    @staticmethod
    def count_completed_tasks(db: Session) -> int:
        """Return the number of tasks with status 'completed'."""
        stmt = select(func.count()).select_from(Task).where(Task.status == "completed")
        return db.scalar(stmt) or 0

    @staticmethod
    def count_pending_tasks(db: Session) -> int:
        """Return the number of tasks with status 'pending'."""
        stmt = select(func.count()).select_from(Task).where(Task.status == "pending")
        return db.scalar(stmt) or 0

    @staticmethod
    def count_inactive_projects(db: Session) -> int:
        """Return the number of inactive projects."""
        stmt = select(func.count()).select_from(Project).where(Project.active.is_(False))
        return db.scalar(stmt) or 0

    @staticmethod
    def get_project_statistics(db: Session) -> dict[str, int]:
        """Return a breakdown of project counts by active status."""
        return {
            "total": DashboardRepository.count_projects(db),
            "active": DashboardRepository.count_active_projects(db),
            "inactive": DashboardRepository.count_inactive_projects(db),
        }

    @staticmethod
    def count_tasks_by_status(db: Session, status: str) -> int:
        """Return the number of tasks matching the given status."""
        stmt = select(func.count()).select_from(Task).where(Task.status == status)
        return db.scalar(stmt) or 0

    @staticmethod
    def get_task_status_breakdown(db: Session) -> dict[str, int]:
        """Return a breakdown of task counts by status."""
        statuses = ["pending", "in_progress", "completed", "blocked"]
        return {
            status: DashboardRepository.count_tasks_by_status(db, status)
            for status in statuses
        }

    @staticmethod
    def count_notes(db: Session) -> int:
        """Return the total number of notes."""
        stmt = select(func.count()).select_from(Note)
        return db.scalar(stmt) or 0

    @staticmethod
    def count_active_resumes(db: Session) -> int:
        """Return the number of resumes marked as available."""
        stmt = (
            select(func.count())
            .select_from(Resume)
            .where(Resume.available.is_(True))
        )
        return db.scalar(stmt) or 0


dashboard_repository = DashboardRepository()
