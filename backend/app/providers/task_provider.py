"""
Mission Control Task Provider

Returns aggregated task data for the dashboard.
Supports sorting and filtering by status and priority.
"""

import logging

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.db.task import Task

logger = logging.getLogger(__name__)


class TaskProvider:
    """Return task statistics and data for the dashboard."""

    def get_task_data(self, db: Session) -> dict:
        """Return task count, status breakdown, and recent items."""
        total = db.scalar(
            select(func.count()).select_from(Task)
        ) or 0

        statuses = ["pending", "in_progress", "completed", "blocked"]
        breakdown = {}
        for status in statuses:
            breakdown[status] = db.scalar(
                select(func.count()).select_from(Task).where(Task.status == status)
            ) or 0

        priorities = ["high", "medium", "low"]
        priority_breakdown = {}
        for priority in priorities:
            priority_breakdown[priority] = db.scalar(
                select(func.count()).select_from(Task).where(Task.priority == priority)
            ) or 0

        recent = (
            db.query(Task)
            .options(selectinload(Task.project))
            .order_by(Task.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "count": total,
            "statistics": {
                "total": total,
                "pending": breakdown["pending"],
                "in_progress": breakdown["in_progress"],
                "completed": breakdown["completed"],
                "blocked": breakdown["blocked"],
            },
            "priority_statistics": {
                "high": priority_breakdown["high"],
                "medium": priority_breakdown["medium"],
                "low": priority_breakdown["low"],
            },
            "items": [self._serialize(t) for t in recent],
        }

    @staticmethod
    def _serialize(task: Task) -> dict:
        project_name = task.project.name if task.project else None
        return {
            "id": str(task.id),
            "project_id": str(task.project_id),
            "project_name": project_name,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }


task_provider = TaskProvider()
