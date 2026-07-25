"""
Mission Control Agent Veeam Provider

Reads Veeam inventory from agent-collected remote target data
stored in Agent.inventory_json.  Implements VeeamProvider so the
existing Veeam pages work transparently for agent-relayed hosts.

Write operations (start/stop job) dispatch commands to the agent
via the server's command queue.
"""

import json
import logging

from .base_provider import VeeamProvider

logger = logging.getLogger(__name__)


class AgentVeeamProvider(VeeamProvider):
    """Veeam provider backed by agent remote inventory data."""

    def __init__(
        self,
        inventory: dict,
        target_hostname: str = "",
        agent_id: int | None = None,
        target_id: int | None = None,
        dispatch_cmd: callable | None = None,
    ) -> None:
        self._inventory = inventory or {}
        self._hostname = target_hostname
        self._agent_id = agent_id
        self._target_id = target_id
        self._dispatch_cmd = dispatch_cmd

    def _get_items(self, key: str) -> list[dict]:
        raw = self._inventory.get(key, [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = []
        if isinstance(raw, dict):
            raw = [raw]
        return raw

    async def _dispatch(self, command_str: str) -> dict:
        if not self._dispatch_cmd:
            return {"success": False, "error": "No agent dispatch available for this host"}
        try:
            return await self._dispatch_cmd(command_str)
        except Exception as e:
            logger.exception("Agent dispatch failed for target %s", self._target_id)
            return {"success": False, "error": str(e)}

    async def test_connection(self) -> dict:
        return {
            "connected": True,
            "latency_ms": 0,
            "message": f"Agent-relayed connection to {self._hostname}",
            "hostname": self._hostname,
            "version": "agent",
        }

    async def get_summary(self) -> dict:
        jobs = self._get_items("jobs")
        sessions = self._get_items("sessions")
        repos = self._get_items("repositories")
        running = sum(1 for j in jobs if (j.get("status") or "").lower() in ("running", "working"))
        successful = sum(1 for s in sessions if (s.get("status") or "").lower() == "success")
        failed = sum(1 for s in sessions if (s.get("status") or "").lower() == "failed")
        return {
            "connected": True,
            "hostname": self._hostname,
            "version": "agent",
            "jobs": len(jobs),
            "running_jobs": running,
            "sessions": len(sessions),
            "successful_sessions": successful,
            "failed_sessions": failed,
            "repositories": len(repos),
            "managed_servers": len(self._get_items("managed_servers")),
            "restore_points": len(self._get_items("restore_points")),
            "backup_size_gb": 0,
            "capacity_tier_configured": False,
            "license_expiry": None,
        }

    async def get_jobs(self) -> dict:
        jobs = self._get_items("jobs")
        return {"connected": True, "count": len(jobs), "items": jobs}

    async def get_job_detail(self, job_id: str) -> dict:
        jobs = self._get_items("jobs")
        for j in jobs:
            if str(j.get("id", j.get("name", ""))) == job_id:
                return {"connected": True, "item": j}
        return {"connected": False, "error": "Job not found in agent inventory"}

    async def get_sessions(self) -> dict:
        sessions = self._get_items("sessions")
        return {"connected": True, "count": len(sessions), "items": sessions[:100]}

    async def get_repositories(self) -> dict:
        repos = self._get_items("repositories")
        return {"connected": True, "count": len(repos), "items": repos}

    async def get_managed_servers(self) -> dict:
        servers = self._get_items("managed_servers")
        return {"connected": True, "count": len(servers), "items": servers}

    async def get_restore_points(self, vm_id: str | None = None) -> dict:
        points = self._get_items("restore_points")
        return {"connected": True, "count": len(points), "items": points[:200]}

    async def get_license(self) -> dict:
        return {"connected": True, "license": self._inventory.get("license", {})}

    async def get_capacity_tier(self) -> dict:
        return {"connected": True, "capacity_tier": self._inventory.get("capacity_tier")}

    async def start_job(self, job_id: str) -> dict:
        return await self._dispatch(f"start_job:{job_id}")

    async def stop_job(self, job_id: str) -> dict:
        return await self._dispatch(f"stop_job:{job_id}")

    async def get_health(self) -> dict:
        return {
            "connected": True,
            "status": "healthy",
            "hostname": self._hostname,
            "version": "agent",
        }

    async def get_session_stats(self) -> dict:
        return {"connected": True, "ssh_available": False, "sessions": []}

    async def get_job_stats(self) -> dict:
        return {"connected": True, "ssh_available": False, "stats": []}

    async def get_job_stats_daily(self, days: int = 7) -> dict:
        return {"connected": True, "ssh_available": False, "stats": []}
