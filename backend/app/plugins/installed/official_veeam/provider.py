"""VeeamServerProvider: one capability-based provider per server row."""

import json
import logging
from typing import Any

from app.plugins.installed.official_veeam import sql_queries  # noqa: F401
from app.plugins.installed.official_veeam.db_probe import run_db_query  # noqa: F401
from app.plugins.installed.official_veeam.rest_client import (
    VeeamRestClient,
    _extract_items,
)
from app.plugins.installed.official_veeam.ssh_executor import build_ssh_executor

logger = logging.getLogger("plugin.veeam.provider")

_JOBS_GROUP = {"jobs", "sessions", "job_stats", "session_stats", "job_stats_daily"}
_META_GROUP = {"repositories", "managed_servers", "license", "capacity_tier", "health", "summary", "restore_points"}
_CONTROL_GROUP = {"start_job", "stop_job"}


def _rest_for(group: str, edition: str, data_source: str) -> bool:
    """True when ``group`` should be served by the REST API."""
    if edition == "community":
        return False
    if group in _JOBS_GROUP:
        return data_source == "api"
    return data_source in ("api", "both")


def _agent_for(group: str, edition: str, data_source: str) -> bool:
    return not _rest_for(group, edition, data_source)


def resolve_server_creds(db: Any, server: Any) -> dict[str, Any]:
    """Resolve runtime credentials for a server row."""
    from app.core.config import get_settings
    from app.core.security import CredentialCipher

    cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
    rest_password = ""
    if server.rest_password_encrypted:
        try:
            rest_password = cipher.decrypt(server.rest_password_encrypted)
        except Exception:
            rest_password = ""
    return {
        "agent_id": server.agent_id,
        "target_id": server.target_id,
        "rest_url": server.rest_url,
        "rest_username": server.rest_username,
        "rest_password": rest_password,
    }


class VeeamServerProvider:
    """Per-server provider with capability-based routing."""

    def __init__(
        self,
        server: Any,
        db: Any,
        executor: Any = None,
        rest: Any = None,
    ) -> None:
        self.server = server
        self._db = db
        self._executor = executor
        self._rest = rest

    # -- lazy construction ------------------------------------------------ #

    @property
    def executor(self) -> Any:
        if self._executor is None:
            self._executor = build_ssh_executor(self._db, self.server)
        return self._executor

    @property
    def rest(self) -> Any:
        if self._rest is None:
            creds = resolve_server_creds(self._db, self.server)
            self._rest = VeeamRestClient(
                base_url=creds["rest_url"],
                username=creds["rest_username"],
                password=creds["rest_password"],
                verify_ssl=self.server.verify_ssl,
                timeout=self.server.timeout or 30,
            )
        return self._rest

    @property
    def edition(self) -> str:
        return self.server.edition

    @property
    def data_source(self) -> str:
        return self.server.data_source

    def _agent(self, group: str) -> bool:
        return _agent_for(group, self.edition, self.data_source)

    def _rest_selected(self, group: str) -> bool:
        return _rest_for(group, self.edition, self.data_source)

    # -- connection ------------------------------------------------------- #

    async def test_connection(self) -> dict[str, Any]:
        from app.plugins.installed.official_veeam.diagnostics import (
            run_connection_diagnostics,
        )
        return await run_connection_diagnostics(self)

    async def get_health(self) -> dict[str, Any]:
        if self.edition == "community":
            result = await self.executor.run("veeam:test")
            if not result.get("success"):
                return {"healthy": False, "error": result.get("error", "Agent probe failed")}
            payload = _json_payload(result)
            return {
                "healthy": bool(payload.get("rest_available") or payload.get("powershell_available")),
                "version": payload.get("version", ""),
                "name": self.server.name,
                "error": payload.get("error"),
            }
        info = await self.rest.test()
        return {
            "healthy": info.get("connected", False),
            "version": info.get("version", ""),
            "name": info.get("name", ""),
            "error": info.get("error"),
        }

    # -- jobs / sessions --------------------------------------------------- #

    async def get_jobs(self) -> dict[str, Any]:
        if self._agent("jobs"):
            result = await self.executor.run("veeam:jobs")
            payload = _json_payload(result)
            items = payload.get("jobs", [])
            return {"success": result.get("success", False), "jobs": items,
                    "count": len(items), "server_names": [self.server.name],
                    "error": result.get("error")}
        data = await self.rest.get("/api/v1/jobs")
        items = _extract_items(data)
        return {"success": True, "jobs": items, "count": len(items),
                "server_names": [self.server.name], "error": None}

    async def get_job_detail(self, job_id: str) -> dict[str, Any]:
        try:
            data = await self.rest.get(f"/api/v1/jobs/{job_id}")
            return {"success": True, "job": data, "error": None}
        except Exception as exc:
            return {"success": False, "job": None, "error": str(exc)}

    async def get_sessions(self) -> dict[str, Any]:
        if self._agent("sessions"):
            result = await self.executor.run("veeam:sessions")
            payload = _json_payload(result)
            items = payload.get("sessions", [])
            return {"success": result.get("success", False), "sessions": items,
                    "count": len(items), "server_names": [self.server.name],
                    "error": result.get("error")}
        data = await self.rest.get("/api/v1/sessions")
        items = _extract_items(data)
        return {"success": True, "sessions": items, "count": len(items),
                "server_names": [self.server.name], "error": None}

    # -- stats (agent unless REST mode; REST has no stats endpoint) -------- #

    async def get_job_stats(self) -> dict[str, Any]:
        return await self._stats_via_agent("job_stats", "jobs")

    async def get_session_stats(self) -> dict[str, Any]:
        return await self._stats_via_agent("session_stats", "stats")

    async def get_job_stats_daily(self, days: int = 7) -> dict[str, Any]:
        if self._rest_selected("job_stats_daily"):
            return {"success": True, "jobs": [], "dates": [], "count": 0,
                    "server_names": [self.server.name], "ssh_available": False,
                    "message": None, "error": None}
        result = await self.executor.run("veeam:job_stats_daily", params={"days": days})
        payload = _json_payload(result)
        return {
            "success": result.get("success", False),
            "jobs": payload.get("jobs", []),
            "dates": payload.get("dates", []),
            "server_names": [self.server.name],
            "ssh_available": result.get("success", False),
            "count": len(payload.get("jobs", [])),
            "message": None,
            "error": result.get("error"),
        }

    async def _stats_via_agent(self, op: str, key: str) -> dict[str, Any]:
        if self._rest_selected(op):
            return {"success": True, key: [], "server_names": [self.server.name],
                    "ssh_available": False, "count": 0, "message": None, "error": None}
        result = await self.executor.run(f"veeam:{op}")
        payload = _json_payload(result)
        return {
            "success": result.get("success", False),
            key: payload.get(key, []),
            "server_names": [self.server.name],
            "ssh_available": result.get("success", False),
            "count": len(payload.get(key, [])),
            "message": None,
            "error": result.get("error"),
        }

    # -- metadata ----------------------------------------------------------- #

    async def get_repositories(self) -> dict[str, Any]:
        return await self._meta("veeam:repositories", "/api/v1/backupInfrastructure/repositories", "repositories")

    async def get_managed_servers(self) -> dict[str, Any]:
        return await self._meta("veeam:managed_servers", "/api/v1/backupInfrastructure/managedServers", "servers")

    async def get_license(self) -> dict[str, Any]:
        if self._rest_selected("license"):
            data = await self.rest.get("/api/v1/license")
            return {"success": True, "license": data, "error": None}
        result = await self.executor.run("veeam:license")
        payload = _json_payload(result)
        return {"success": result.get("success", False), "license": payload.get("license", {}),
                "error": result.get("error")}

    async def get_capacity_tier(self) -> dict[str, Any]:
        return await self._meta("veeam:capacity_tier", "/api/v1/backupInfrastructure/objectStorages", "object_storages")

    async def get_restore_points(self, vm_id: str | None = None) -> dict[str, Any]:
        if self._rest_selected("restore_points"):
            data = await self.rest.get("/api/v1/restorePoints")
            items = _extract_items(data)
            if vm_id:
                items = [r for r in items if r.get("vmId") == vm_id]
            return {"success": True, "restore_points": items, "count": len(items), "error": None}
        result = await self.executor.run("veeam:restore_points")
        payload = _json_payload(result)
        items = payload.get("restore_points", [])
        if vm_id:
            items = [r for r in items if r.get("vm_id") == vm_id or r.get("vmId") == vm_id]
        return {"success": result.get("success", False), "restore_points": items,
                "count": len(items), "error": result.get("error")}

    async def _meta(self, op: str, rest_path: str, key: str) -> dict[str, Any]:
        if self._rest_selected(key):
            data = await self.rest.get(rest_path)
            items = _extract_items(data)
            return {"success": True, key: items, "count": len(items), "error": None}
        result = await self.executor.run(op)
        payload = _json_payload(result)
        items = payload.get(key, [])
        return {"success": result.get("success", False), key: items,
                "count": len(items), "error": result.get("error")}

    # -- job control --------------------------------------------------------- #

    async def start_job(self, job_id: str) -> dict[str, Any]:
        if self._rest_selected("start_job"):
            try:
                await self.rest.post(f"/api/v1/jobs/{job_id}/start")
                return {"success": True, "message": f"Job {job_id} started", "error": None}
            except Exception as exc:
                return {"success": False, "message": None, "error": str(exc)}
        result = await self.executor.run("veeam:start_job", params={"job_id": job_id})
        return {"success": result.get("success", False), "message": result.get("message"),
                "error": result.get("error")}

    async def stop_job(self, job_id: str) -> dict[str, Any]:
        if self._rest_selected("stop_job"):
            try:
                await self.rest.post(f"/api/v1/jobs/{job_id}/stop")
                return {"success": True, "message": f"Job {job_id} stopped", "error": None}
            except Exception as exc:
                return {"success": False, "message": None, "error": str(exc)}
        result = await self.executor.run("veeam:stop_job", params={"job_id": job_id})
        return {"success": result.get("success", False), "message": result.get("message"),
                "error": result.get("error")}

    # -- summary --------------------------------------------------------------- #

    async def get_summary(self) -> dict[str, Any]:
        jobs = await self.get_jobs()
        repos = await self.get_repositories()
        sessions = await self.get_sessions()
        job_items = jobs.get("jobs", [])
        repo_items = repos.get("repositories", [])
        session_items = sessions.get("sessions", [])
        running = sum(1 for j in job_items if str(j.get("state", "")).lower() == "running")
        result_map = {"Success": "success", "Warning": "warning", "Failed": "failed"}
        counts = {"success": 0, "warning": 0, "failed": 0}
        for s in session_items:
            r = s.get("result", {})
            if isinstance(r, dict):
                counts[result_map.get(r.get("result", ""), "success")] += 1
        total_space = 0
        used_space = 0
        for r in repo_items:
            total_space += r.get("capacityBytes", 0) or r.get("repository", {}).get("capacityBytes", 0)
            used_space += r.get("usedSpaceBytes", 0) or r.get("repository", {}).get("usedSpaceBytes", 0)
        info = await self.get_health()
        return {
            "success": jobs.get("success", False) and repos.get("success", False),
            "version": info.get("version", ""),
            "name": info.get("name", self.server.name),
            "total_jobs": len(job_items),
            "running_jobs": running,
            "total_repositories": len(repo_items),
            "total_space_bytes": total_space,
            "used_space_bytes": used_space,
            "recent_sessions": len(session_items),
            "sessions_success": counts["success"],
            "sessions_warning": counts["warning"],
            "sessions_failed": counts["failed"],
            "error": None,
        }


def build_server_provider(db: Any, server: Any) -> VeeamServerProvider:
    """Build a provider for a server row, validating required fields."""
    if server.edition == "community":
        if server.agent_id is None or server.target_id is None:
            raise ValueError("Community Veeam requires an agent and remote target")
    elif server.data_source in ("api", "both") and not server.rest_url:
        raise ValueError("Enterprise API/both requires a REST URL")
    return VeeamServerProvider(db=db, server=server)


def _json_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Parse the executor's stdout JSON result."""
    output = result.get("output", "")
    if not output:
        return {}
    try:
        data = json.loads(output)
        return data if isinstance(data, dict) else {"items": data}
    except (ValueError, TypeError):
        return {"error": "Agent returned non-JSON output"}
