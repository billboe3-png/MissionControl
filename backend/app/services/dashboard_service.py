"""
Mission Control Dashboard Service

Orchestrator that delegates to individual providers.
Contains NO business logic — only aggregation.

Sprint 2.0 - Refactored to orchestrator pattern.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.providers.health_provider import health_provider
from app.providers.system_provider import system_provider
from app.providers.docker_provider import docker_provider
from app.providers.git_provider import git_provider
from app.providers.project_provider import project_provider
from app.providers.task_provider import task_provider
from app.providers.note_provider import note_provider
from app.providers.resume_provider import resume_provider
from app.providers.parking_lot_provider import parking_lot_provider

logger = logging.getLogger(__name__)


class DashboardService:
    """Orchestrates dashboard data from all providers."""

    async def get_dashboard(self, db: Session) -> dict:
        """
        Aggregate all provider data into a single dashboard response.

        Each provider handles its own data access and error handling.
        The orchestrator combines results without containing business logic.
        """
        logger.info("Loading dashboard data from providers")

        health = await health_provider.get_health(db)
        system = system_provider.get_system_info()
        docker = await docker_provider.get_docker_data()
        git = git_provider.get_git_info()
        projects = project_provider.get_project_data(db)
        tasks = task_provider.get_task_data(db)
        notes = note_provider.get_note_data(db)
        resume = resume_provider.get_resume_data(db)
        parking_lot = parking_lot_provider.get_parking_lot_data(db)

        return {
            "application": {
                "name": "Mission Control",
                "tagline": "The Daily Workspace for IT Operations",
                "version": "2.0.0",
            },
            "generated": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "projects": projects["count"],
                "active_projects": projects["statistics"]["active"],
                "tasks": tasks["count"],
                "completed_tasks": tasks["statistics"]["completed"],
                "pending_tasks": tasks["statistics"]["pending"],
                "notes": notes["count"],
                "resume_available": resume["available"],
                "containers_running": docker["running"],
                "containers_total": docker["container_count"],
                "docker_engine": docker["engine"],
            },
            "health": health,
            "system": system,
            "docker": docker,
            "git": git,
            "projects": projects,
            "tasks": tasks,
            "notes": notes,
            "resume": resume,
            "parking_lot": parking_lot,
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
