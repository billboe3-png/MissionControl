"""
Mission Control Project Provider

Returns aggregated project data for the dashboard.
Supports search, sort, and filter operations.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.project import Project

logger = logging.getLogger(__name__)


class ProjectProvider:
    """Return project statistics and data for the dashboard."""

    def get_project_data(self, db: Session) -> dict:
        """Return project count, statistics, and recent items."""
        total = db.scalar(
            select(func.count()).select_from(Project)
        ) or 0
        active = db.scalar(
            select(func.count()).select_from(Project).where(Project.active.is_(True))
        ) or 0
        inactive = total - active

        recent = (
            db.query(Project)
            .order_by(Project.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "count": total,
            "statistics": {
                "total": total,
                "active": active,
                "inactive": inactive,
            },
            "items": [self._serialize(p) for p in recent],
        }

    @staticmethod
    def _serialize(project: Project) -> dict:
        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "active": project.active,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }


project_provider = ProjectProvider()
