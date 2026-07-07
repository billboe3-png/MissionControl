"""
Mission Control Summary Service

Provides summary KPI information for the dashboard.

Sprint:
    1.1.0 - Dashboard Experience
"""

from app.services.integrations_service import integrations_service
from app.services.note_service import note_service
from app.services.project_service import project_service
from app.services.resume_service import resume_service
from app.services.task_service import task_service


class SummaryService:
    """Dashboard summary KPI section."""

    async def get_data(self) -> dict:

        integrations = await integrations_service.get_data()

        docker = integrations["docker"]

        projects = await project_service.get_data()
        tasks = await task_service.get_data()
        notes = await note_service.get_data()
        resume = await resume_service.get_data()

        return {
            "containers_running": docker.get("container_count", 0),
            "containers_total": docker.get("container_count", 0),
            "docker_engine": docker.get("engine", "offline"),
            "projects": projects["count"],
            "tasks": tasks["count"],
            "notes": notes["count"],
            "resume_available": resume is not None,
        }


summary_service = SummaryService()
