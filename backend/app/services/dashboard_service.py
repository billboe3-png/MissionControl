"""
Mission Control Dashboard Service

Aggregates all dashboard services into a single payload.

Sprint:
    1.0.3
"""

from datetime import datetime, timezone

from app.services.docker_service import get_docker_status
from app.services.project_service import project_service
from app.services.task_service import task_service
from app.services.note_service import note_service
from app.services.resume_service import resume_service


class DashboardService:
    """Service responsible for building the dashboard response."""

    async def get_dashboard(self) -> dict:
        """Return the complete dashboard payload."""

        docker = await get_docker_status()
        projects = await project_service.get_data()
        tasks = await task_service.get_data()
        notes = await note_service.get_data()
        resume = await resume_service.get_data()

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
                "projects": projects["count"],
                "tasks": tasks["count"],
                "notes": notes["count"],
                "resume_available": resume["available"],
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
