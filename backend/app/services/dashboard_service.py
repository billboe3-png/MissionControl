"""
Mission Control Dashboard Service

Orchestrator that delegates to domain services.
Contains NO business logic — only aggregation.

Dashboard → Dashboard Aggregator → Agent Service, Plugin Service,
Inventory Service, Alert Service, Automation Service, AI Service.

Sprint 2.0 - Refactored to orchestrator pattern.
Sprint 2.3.0 - Added Zabbix integration.
Sprint 3.2B - Agent-first architecture, service delegation.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.providers.health_provider import health_provider
from app.providers.note_provider import note_provider
from app.providers.parking_lot_provider import parking_lot_provider
from app.providers.project_provider import project_provider
from app.providers.remote_provider import RemoteProvider
from app.providers.resume_provider import resume_provider
from app.providers.task_provider import task_provider

logger = logging.getLogger(__name__)


class DashboardService:
    """Orchestrates dashboard data from domain services."""

    def __init__(self) -> None:
        self._remote_provider = RemoteProvider()

    async def get_dashboard(self, db: Session) -> dict:
        """
        Aggregate all domain service data into a single dashboard response.

        Each domain service handles its own data access and error handling.
        The orchestrator combines results without containing business logic.
        """
        logger.info("Loading dashboard data from domain services")

        health = await health_provider.get_health(db)
        projects = project_provider.get_project_data(db)
        tasks = task_provider.get_task_data(db)
        notes = note_provider.get_note_data(db)
        resume = resume_provider.get_resume_data(db)
        parking_lot = parking_lot_provider.get_parking_lot_data(db)
        remote = await self._remote_provider.get_remote_data(db)
        zabbix = await self._get_zabbix_data(db)
        veeam = await self._get_veeam_data(db)
        unifi = await self._get_unifi_data(db)
        docker = await self._get_docker_data(db)
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
                "zabbix_hosts": zabbix.get("host_count", 0),
                "zabbix_problems": zabbix.get("problem_count", 0),
                "zabbix_critical": zabbix.get("critical_count", 0),
                "veeam_servers": veeam.get("server_count", 0),
                "veeam_jobs": veeam.get("job_count", 0),
                "veeam_repositories": veeam.get("repository_count", 0),
                "unifi_controllers": unifi.get("controller_count", 0),
                "unifi_devices": unifi.get("device_count", 0),
                "unifi_online_devices": unifi.get("online_devices", 0),
                "unifi_clients": unifi.get("client_count", 0),
                "docker_hosts": docker.get("host_count", 0),
                "docker_containers": docker.get("container_count", 0),
                "docker_running": docker.get("running", 0),
                "docker_unhealthy": docker.get("unhealthy", 0),
                "agents_online": agents["online"],
                "agents_total": agents["total"],
            },
            "health": health,
            "projects": projects,
            "tasks": tasks,
            "notes": notes,
            "resume": resume,
            "parking_lot": parking_lot,
            "remote": remote,
            "zabbix": zabbix,
            "veeam": veeam,
            "unifi": unifi,
            "docker": docker,
            "hyperv": hyperv,
            "proxmox": proxmox,
            "integrations": integrations,
            "agents": agents,
            "automation": automation,
            "ai": ai,
            "git": {
                "available": False,
                "repository_name": None,
                "current_branch": None,
                "latest_commit": None,
                "commit_author": None,
                "commit_date": None,
                "working_tree_clean": False,
                "ahead_of_origin": 0,
                "behind_origin": 0,
                "last_pull": None,
                "remote_url": None,
                "reason": "Git repository information is not collected by this deployment.",
            },
        }

    async def _get_zabbix_data(self, db: Session) -> dict:
        """Get Zabbix data, preferring plugin cache over live provider."""
        # Prefer plugin-provided data (cached from background sync)
        try:
            from app.plugins.registry import plugin_registry

            if plugin_registry.has_plugin("zabbix"):
                return await plugin_registry.get_widget_data(
                    "zabbix", "zabbix-summary"
                )
        except Exception:
            pass

        # Fall back to direct provider call
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

    async def _get_veeam_data(self, db: Session) -> dict:
        """Get Veeam data, preferring plugin cache over live provider."""
        try:
            from app.plugins.registry import plugin_registry

            if plugin_registry.has_plugin("official_veeam"):
                return await plugin_registry.get_widget_data(
                    "official_veeam", "veeam-summary"
                )
        except Exception:
            pass

        try:
            from app.providers.veeam.provider_factory import get_veeam_provider

            provider = get_veeam_provider(db)
            return await provider.get_summary()
        except Exception as e:
            logger.warning("Dashboard: Veeam data failed: %s", e)
            return {
                "connected": False,
                "server_count": 0,
                "repository_count": 0,
                "job_count": 0,
                "restore_point_count": 0,
                "total_space_bytes": 0,
                "free_space_bytes": 0,
            }

    async def _get_unifi_data(self, db: Session) -> dict:
        """Get UniFi data, preferring plugin cache over live provider."""
        try:
            from app.plugins.registry import plugin_registry

            if plugin_registry.has_plugin("official_unifi"):
                return await plugin_registry.get_widget_data(
                    "official_unifi", "unifi-summary"
                )
        except Exception:
            pass

        try:
            from app.plugins.installed.official_unifi.cache import cache_manager

            return cache_manager.get_summary(db)
        except Exception as e:
            logger.warning("Dashboard: UniFi data failed: %s", e)
            return {
                "connected": False,
                "controller_count": 0,
                "site_count": 0,
                "device_count": 0,
                "online_devices": 0,
                "offline_devices": 0,
                "client_count": 0,
                "alert_count": 0,
                "wireless_network_count": 0,
            }

    async def _get_docker_data(self, db: Session) -> dict:
        """Get Docker data, preferring plugin cache."""
        try:
            from app.plugins.registry import plugin_registry

            if plugin_registry.has_plugin("official_docker"):
                return await plugin_registry.get_widget_data(
                    "official_docker", "docker-summary"
                )
        except Exception:
            pass

        try:
            from app.plugins.installed.official_docker.cache import cache_manager

            return cache_manager.get_summary(db)
        except Exception as e:
            logger.warning("Dashboard: Docker data failed: %s", e)
            return {
                "connected": False,
                "host_count": 0,
                "container_count": 0,
                "running": 0,
                "stopped": 0,
                "unhealthy": 0,
                "image_count": 0,
                "volume_count": 0,
                "network_count": 0,
            }

    async def _get_hyperv_data(self, db: Session) -> dict:
        """Get Hyper-V data via provider factory, never raise."""
        try:
            from app.providers.hyperv.provider_factory import get_hyperv_provider

            provider = get_hyperv_provider(db)
            return await provider.get_summary()
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
        """Get Proxmox data via provider factory, never raise."""
        try:
            from app.providers.proxmox.provider_factory import get_proxmox_provider

            provider = get_proxmox_provider(db)
            return await provider.get_summary()
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

    async def _get_integrations_data(self, db: Session) -> dict:
        """Delegate to IntegrationService, never raise."""
        try:
            from app.services.integration_service import integration_service

            return await integration_service.get_dashboard_summary(db)
        except Exception as e:
            logger.warning("Dashboard: integrations data failed: %s", e)
            return {"count": 0, "items": []}

    async def _get_agent_data(self, db: Session) -> dict:
        """Delegate to AgentService, never raise."""
        try:
            from app.services.agent_service import agent_service

            return await agent_service.get_dashboard_summary(db)
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
        """Delegate to AI Service, never raise."""
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
        """Delegate to AutomationService, never raise."""
        try:
            from app.services.automation_service import automation_service

            return await automation_service.get_automation_summary(db)
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
