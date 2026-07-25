"""
Mission Control Dashboard Service

Orchestrator that delegates to individual providers.
Contains NO business logic — only aggregation.

Sprint 2.0 - Refactored to orchestrator pattern.
Sprint 2.3.0 - Added Zabbix integration.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.providers.docker_provider import docker_provider
from app.providers.git_provider import git_provider
from app.providers.health_provider import health_provider
from app.providers.note_provider import note_provider
from app.providers.parking_lot_provider import parking_lot_provider
from app.providers.project_provider import project_provider
from app.providers.remote_provider import RemoteProvider
from app.providers.resume_provider import resume_provider
from app.providers.system_provider import system_provider
from app.providers.task_provider import task_provider

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
        zabbix = await self._get_zabbix_data(db)
        hyperv = await self._get_hyperv_data(db)
        proxmox = await self._get_proxmox_data(db)
        integrations = await self._get_integrations_data(db)
        agents = await self._get_agent_data(db)
        ai = await self._get_ai_data(db)
        automation = await self._get_automation_data(db)

        return {
            "application": {
                "name": "Mission Control",
                "tagline": "The Daily Workspace for IT Operations",
                "version": "3.0.0",
            },
            "generated": datetime.now(UTC).isoformat(),
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
                "agents_online": agents["online"],
                "agents_total": agents["total"],
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
            "hyperv": hyperv,
            "proxmox": proxmox,
            "integrations": integrations,
            "agents": agents,
            "automation": automation,
            "ai": ai,
        }

    async def _get_zabbix_data(self, db: Session) -> dict:
        """Get Zabbix data for the dashboard, never raise."""
        try:
            from app.providers.zabbix.provider_factory import get_zabbix_provider

            provider = get_zabbix_provider(db)
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

    async def _get_hyperv_data(self, db: Session) -> dict:
        """Get Hyper-V data for the dashboard, never raise."""
        try:
            from app.providers.hyperv_dashboard import (
                virtualization_dashboard_provider,
            )

            return await virtualization_dashboard_provider.get_virtualization_data(db)
        except Exception as e:
            logger.warning("Dashboard: Hyper-V data failed: %s", e)
            return {
                "connected": False,
                "total_vms": 0,
                "running": 0,
                "stopped": 0,
                "total_memory_gb": 0,
                "used_memory_gb": 0,
            }

    async def _get_proxmox_data(self, db: Session) -> dict:
        """Get Proxmox data for the dashboard, never raise."""
        try:
            from app.providers.proxmox_dashboard import proxmox_dashboard_provider

            return await proxmox_dashboard_provider.get_proxmox_data(db)
        except Exception as e:
            logger.warning("Dashboard: Proxmox data failed: %s", e)
            return {
                "connected": False,
                "total_vms": 0,
                "running": 0,
                "stopped": 0,
                "total_memory_gb": 0,
                "used_memory_gb": 0,
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

    async def _get_agent_data(self, db: Session) -> dict:
        """Get agent stats for the dashboard, never raise."""
        try:
            from sqlalchemy import func, select

            from app.models.db.agent import Agent

            row = db.execute(
                select(
                    func.count(Agent.id).label("total"),
                    func.count(Agent.id).filter(Agent.status == "online").label("online"),
                    func.avg(Agent.cpu_percent).filter(
                        Agent.status == "online", Agent.cpu_percent.isnot(None)
                    ).label("avg_cpu"),
                    func.avg(Agent.memory_percent).filter(
                        Agent.status == "online", Agent.memory_percent.isnot(None)
                    ).label("avg_mem"),
                )
            ).one()

            total = row.total or 0
            online = row.online or 0
            avg_cpu = row.avg_cpu
            avg_mem = row.avg_mem

            return {
                "total": total,
                "online": online,
                "offline": total - online,
                "avg_cpu": round(float(avg_cpu), 1) if avg_cpu else 0,
                "avg_memory": round(float(avg_mem), 1) if avg_mem else 0,
            }
        except Exception as e:
            logger.warning("Dashboard: agent data failed: %s", e)
            return {
                "total": 0,
                "online": 0,
                "offline": 0,
                "avg_cpu": 0,
                "avg_memory": 0,
            }

    async def _get_ai_data(self, db: Session) -> dict:
        """Get AI overview data for the dashboard, never raise."""
        try:
            from app.ai.ai_service import ai_service

            return await ai_service.get_overview(db)
        except Exception as e:
            logger.warning("Dashboard: AI data failed: %s", e)
            return {
                "health_score": {"score": 0, "grade": "N/A"},
                "critical_incidents": 0,
                "recommendations": 0,
                "correlated_alerts": 0,
                "top_risks": [],
            }

    async def _get_automation_data(self, db: Session) -> dict:
        """Get automation summary data for the dashboard, never raise."""
        try:
            from sqlalchemy import func

            from app.models.db.approval_request import ApprovalRequest
            from app.models.db.audit_trail import AuditTrail
            from app.models.db.playbook import Playbook
            from app.models.db.playbook_execution import PlaybookExecution

            total_playbooks = db.query(func.count(Playbook.id)).scalar() or 0
            total_executions = db.query(func.count(PlaybookExecution.id)).scalar() or 0
            running = db.query(
                func.count(PlaybookExecution.id)
            ).filter(PlaybookExecution.status == "running").scalar() or 0
            completed = db.query(
                func.count(PlaybookExecution.id)
            ).filter(PlaybookExecution.status == "completed").scalar() or 0
            failed = db.query(
                func.count(PlaybookExecution.id)
            ).filter(PlaybookExecution.status == "failed").scalar() or 0
            pending_approvals = db.query(
                func.count(ApprovalRequest.id)
            ).filter(ApprovalRequest.status == "pending").scalar() or 0
            audit_entries = db.query(func.count(AuditTrail.id)).scalar() or 0

            return {
                "total_playbooks": total_playbooks,
                "total_executions": total_executions,
                "running": running,
                "completed": completed,
                "failed": failed,
                "pending_approvals": pending_approvals,
                "audit_entries": audit_entries,
            }
        except Exception as e:
            logger.warning("Dashboard: automation data failed: %s", e)
            return {
                "total_playbooks": 0,
                "total_executions": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "pending_approvals": 0,
                "audit_entries": 0,
            }


dashboard_service = DashboardService()
