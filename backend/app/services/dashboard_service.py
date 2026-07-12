"""
Mission Control Dashboard Service

Aggregates all dashboard services into a single payload.

Sprint:
    1.0.3
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import dashboard_repository
from app.services.docker_service import get_docker_status
from app.services.project_service import project_service
from app.services.task_service import task_service
from app.services.note_service import note_service
from app.services.resume_service import resume_service

logger = logging.getLogger(__name__)


class DashboardService:
    """Service responsible for building the dashboard response."""

    async def get_dashboard(self, db: Session) -> dict:
        """
        Return the complete dashboard payload.

        Args:
            db: Active SQLAlchemy session provided by the router.
        """
        logger.info("Loading project statistics")
        project_statistics = dashboard_repository.get_project_statistics(db)

        logger.info("Loading task statistics")
        task_breakdown = dashboard_repository.get_task_status_breakdown(db)
        total_tasks = dashboard_repository.count_tasks(db)

        logger.info("Loading dashboard statistics")

        docker = await get_docker_status()
        projects = await project_service.get_data(db)
        tasks = await task_service.get_data(db)
        notes = await note_service.get_data(db)
        resume = await resume_service.get_data(db)

        running = len([c for c in docker["containers"] if c["status"] == "running"])

        return {
            "application": {
                "name": "Mission Control",
                "tagline": "The Daily Workspace for IT Operations",
                "version": "1.0.3",
            },
            "generated": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "containers_running": running,
                "containers_total": docker["container_count"],
                "docker_engine": docker["engine"],
                "projects": project_statistics["total"],
                "active_projects": project_statistics["active"],
                "project_statistics": {
                    "total": project_statistics["total"],
                    "active": project_statistics["active"],
                    "inactive": project_statistics["inactive"],
                },
                "tasks": total_tasks,
                "completed_tasks": task_breakdown["completed"],
                "pending_tasks": task_breakdown["pending"],
                "task_statistics": {
                    "total": total_tasks,
                    "pending": task_breakdown["pending"],
                    "in_progress": task_breakdown["in_progress"],
                    "completed": task_breakdown["completed"],
                    "blocked": task_breakdown["blocked"],
                },
                "notes": dashboard_repository.count_notes(db),
                "resume_available": dashboard_repository.count_active_resumes(db) > 0,
            },
            "health": {
                "backend": {"status": "healthy"},
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
            "projects": projects,
            "tasks": tasks,
            "notes": notes,
            "resume": resume,
            "parking_lot": {
                "count": 0,
                "items": [],
            },
            "integrations": {
                "docker": docker,
                "ssh": {
                    "enabled": False,
                    "status": "not_configured",
                },
                "zabbix": {
                    "enabled": False,
                    "status": "not_configured",
                },
                "github": {
                    "enabled": False,
                    "status": "not_configured",
                },
            },
        }


dashboard_service = DashboardService()
