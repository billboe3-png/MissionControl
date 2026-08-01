"""Agent-local Veeam provider.

Reads Veeam inventory collected by the agent's own Veeam plugin,
without requiring a remote target entry.
"""

import json
import logging
from typing import Any

from .base_provider import VeeamProvider

logger = logging.getLogger(__name__)


class AgentLocalVeeamProvider(VeeamProvider):
    """Veeam provider backed by agent-local plugin inventory."""

    def __init__(self, veeam_inventory: dict[str, Any], target_hostname: str) -> None:
        self._inventory = veeam_inventory or {}
        self._hostname = target_hostname

    @property
    def name(self) -> str:
        return f"{self._hostname} (Agent Local)"

    def _get_items(self, key: str) -> list[dict]:
        raw = self._inventory.get(key, [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = []
        if isinstance(raw, dict):
            raw = [raw]
        return raw if isinstance(raw, list) else []

    async def get_summary(self) -> dict[str, Any]:
        jobs = self._get_items("jobs")
        sessions = self._get_items("sessions")
        running = sum(1 for j in jobs if j.get("state") == "Running")
        failed = sum(1 for s in sessions if "failed" in str(s.get("state", "")).lower())
        return {
            "success": True,
            "server_name": self._hostname,
            "total_jobs": len(jobs),
            "running_jobs": running,
            "failed_sessions": failed,
            "license": self._inventory.get("license", {}),
        }

    async def get_jobs(self) -> dict[str, Any]:
        return {"connected": True, "count": len(self._get_items("jobs")), "items": self._get_items("jobs")}

    async def get_job_detail(self, job_id: str) -> dict[str, Any]:
        for job in self._get_items("jobs"):
            if str(job.get("id")) == str(job_id):
                return {"connected": True, "item": job}
        return {"connected": False, "error": "Job not found in agent inventory"}

    async def get_sessions(self) -> dict[str, Any]:
        return {"connected": True, "count": len(self._get_items("sessions")), "items": self._get_items("sessions")}

    async def get_repositories(self) -> dict[str, Any]:
        return {"connected": True, "count": len(self._get_items("repositories")), "items": self._get_items("repositories")}

    async def get_managed_servers(self) -> dict[str, Any]:
        return {"connected": True, "count": len(self._get_items("managed_servers")), "items": self._get_items("managed_servers")}

    async def get_restore_points(self, vm_id: str | None = None) -> dict[str, Any]:
        points = self._get_items("restore_points")
        return {"connected": True, "count": len(points), "items": points}

    async def get_license(self) -> dict[str, Any]:
        return {"connected": True, "license": self._inventory.get("license", {})}

    async def get_capacity_tier(self) -> dict[str, Any]:
        return {"capacity_tier": self._inventory.get("capacity_tier")}

    async def get_health(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "status": "healthy",
            "hostname": self._hostname,
            "version": "agent",
        }

    async def get_session_stats(self) -> dict[str, Any]:
        return {"connected": True, "ssh_available": False, "sessions": []}

    async def get_job_stats(self) -> dict[str, Any]:
        return {"connected": True, "ssh_available": False, "stats": []}

    async def get_job_stats_daily(self, days: int = 7) -> dict[str, Any]:
        return {"connected": True, "ssh_available": False, "stats": []}

    async def test_connection(self) -> dict[str, Any]:
        return {
            "success": True,
            "available": True,
            "message": "Agent-local Veeam inventory is available",
            "data": self._inventory.get("license", {}),
        }

    async def start_job(self, job_id: str) -> dict[str, Any]:
        return {
            "success": False,
            "error": "Agent-local provider is read-only; use agent command dispatch for control",
        }

    async def stop_job(self, job_id: str) -> dict[str, Any]:
        return {
            "success": False,
            "error": "Agent-local provider is read-only; use agent command dispatch for control",
        }
