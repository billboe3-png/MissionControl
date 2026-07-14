"""
Mission Control Dashboard Service

Orchestrator that delegates to individual providers.
Contains NO business logic — only aggregation.

Sprint 2.0 - Refactored to orchestrator pattern.
Sprint 2.3.0 - Added Zabbix integration.
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
from app.providers.remote_provider import RemoteProvider

logger = logging.getLogger(__name__)


class DashboardService:
    """Orchestrates dashboard data from all providers."""

    def __init__(self) -> None:
        self._remote_provider = RemoteProvider()

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
        remote = await self._remote_provider.get_remote_data(db)
        zabbix = await self._get_zabbix_data()
        integrations = await self._get_integrations_data(db)

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
                "zabbix_hosts": zabbix.get("host_count", 0),
                "zabbix_problems": zabbix.get("problem_count", 0),
                "zabbix_critical": zabbix.get("critical_count", 0),
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
            "remote": remote,
            "zabbix": zabbix,
            "integrations": integrations,
        }

    async def _get_zabbix_data(self) -> dict:
        """Get Zabbix data for the dashboard, never raise."""
        try:
            from app.providers.zabbix.provider_factory import get_zabbix_provider

            provider = get_zabbix_provider()
            return await provider.get_summary()
        except Exception as e:
            logger.warning("Dashboard: Zabbix data failed: %s", e)
            return {
                "connected": False,
                "host_count": 0,
                "problem_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "ok_count": 0,
            }

    async def _get_integrations_data(self, db) -> dict:
        """Get integration statuses for the dashboard."""
        try:
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )

            profiles = IntegrationProfileRepository.get_all(db)
            items = []
            for p in profiles:
                items.append({
                    "id": p.id,
                    "name": p.name,
                    "type": p.integration_type,
                    "enabled": p.enabled,
                    "connected": (
                        p.last_success is not None
                        and p.last_error is None
                    ),
                    "last_test": (
                        p.last_test.isoformat()
                        if p.last_test
                        else None
                    ),
                })
            return {
                "count": len(items),
                "items": items,
            }
        except Exception as e:
            logger.warning(
                "Dashboard: integrations data failed: %s", e
            )
            return {"count": 0, "items": []}


dashboard_service = DashboardService()
