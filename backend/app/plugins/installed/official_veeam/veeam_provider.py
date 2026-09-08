"""
Veeam B&R Provider -- Production

Communicates with Veeam Backup & Replication. When an agent relay is
configured (the production deployment), all data collection is dispatched
through the linked Mission Control agent via ``AgentSshExecutor`` so that
the private Veeam hosts are reached from the agent's LAN. Otherwise it
falls back to direct REST API calls.

Also includes an SSH+PostgreSQL bridge for data the REST API does not
expose (e.g. session transfer statistics), relayed through the agent.
"""

import json
import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.plugins.installed.official_veeam.base_provider import VeeamProvider

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
API_VERSION = "1.3-rev1"


def _extract_items(data: Any) -> list:
    """Extract items from Veeam paginated response."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


class VeeamRESTProvider:
    """Veeam B&R provider (agent-relay or direct REST)."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        ssh_host: str = "",
        ssh_port: int = 22,
        ssh_username: str = "",
        ssh_password: str = "",
        data_source: str = "both",
        db_type: str = "postgresql",
        column_case: str = "pascal",
        db: Any = None,
        server_id: int | None = None,
        agent_id: int | None = None,
        target_id: int | None = None,
    ) -> None:
        parsed = urlparse(base_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        self._server_host = parsed.hostname or ""
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._token: str | None = None
        self._token_expires: float = 0

        # SSH bridge for PostgreSQL/MSSQL queries
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.data_source = data_source
        self.db_type = db_type
        self.column_case = column_case

        # Agent relay context (production path)
        self._db = db
        self.server_id = server_id
        self.agent_id = agent_id
        self.target_id = target_id

    # ------------------------------------------------------------------ #
    # Relay helpers                                                       #
    # ------------------------------------------------------------------ #

    def _has_relay(self) -> bool:
        return bool(self.agent_id is not None and self.target_id is not None)

    async def _relay(self, op: str, params: dict | None = None) -> dict[str, Any]:
        """Dispatch a veeam:* op through the linked agent and return its JSON."""
        from app.plugins.installed.official_veeam.ssh_executor import AgentSshExecutor

        executor = AgentSshExecutor(
            db=self._db,
            agent_id=self.agent_id,
            target_id=self.target_id,
            timeout=120,
        )
        payload = dict(params or {})
        payload.setdefault("db_type", self.db_type)
        result = await executor.run(op=op, params=payload, timeout=120)
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error") or "Agent relay command failed",
            }
        output = result.get("output") or ""
        try:
            payload = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return {
                "success": False,
                "error": "Invalid JSON from agent relay",
                "raw": output[:2000],
            }
        if not isinstance(payload, dict):
            return {"success": False, "error": "Agent relay returned non-object"}
        return payload

    def _relay_or_http(self, op: str, params: dict | None = None, path: str | None = None):
        """Return a callable that relays if possible, else hits REST directly."""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # HTTP helpers (direct fallback)                                      #
    # ------------------------------------------------------------------ #

    async def _get_token(self) -> str:
        """Obtain or refresh an OAuth2 access token."""
        import time

        if self._token and time.time() < self._token_expires - 30:
            return self._token

        async with httpx.AsyncClient(
            verify=self.verify_ssl, timeout=self.timeout
        ) as client:
            resp = await client.post(
                f"{self.base_url}/api/oauth2/token",
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                },
                headers={"x-api-version": API_VERSION},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires = time.time() + data.get("expires_in", 3600)
            return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "x-api-version": API_VERSION,
        }

    async def _get(self, path: str) -> dict[str, Any]:
        await self._get_token()
        async with httpx.AsyncClient(
            verify=self.verify_ssl, timeout=self.timeout
        ) as client:
            resp = await client.get(
                f"{self.base_url}{path}", headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, json: dict | None = None) -> dict[str, Any]:
        await self._get_token()
        async with httpx.AsyncClient(
            verify=self.verify_ssl, timeout=self.timeout
        ) as client:
            resp = await client.post(
                f"{self.base_url}{path}", headers=self._headers(), json=json
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {"success": True}

    # ------------------------------------------------------------------ #
    # Connection                                                          #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:test")
            connected = bool(
                result.get("success")
                or result.get("rest_available")
                or result.get("db_available")
                or result.get("powershell_available")
            )
            return {
                "connected": connected,
                "version": result.get("version", ""),
                "name": result.get("name", ""),
                "server_id": result.get("server_id"),
                "db_available": result.get("db_available", False),
                "rest_available": result.get("rest_available", False),
                "powershell_available": result.get("powershell_available", False),
                "error": None if connected else (result.get("error") or "Relay unavailable"),
            }
        try:
            await self._get_token()
            data = await self._get("/api/v1/serverInfo")
            return {
                "connected": True,
                "version": data.get("buildVersion", ""),
                "name": data.get("name", ""),
                "server_id": data.get("vbrId", ""),
            }
        except Exception as exc:
            logger.exception("Veeam connection test failed")
            return {"connected": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Server info                                                         #
    # ------------------------------------------------------------------ #

    async def get_summary(self) -> dict:
        try:
            jobs = await self.get_jobs()
            sessions = await self.get_sessions()
            repos = await self.get_repositories()

            job_list = jobs.get("jobs", []) or []
            repo_list = repos.get("repositories", []) or []
            session_list = sessions.get("sessions", []) or []

            running = sum(
                1 for j in job_list if str(j.get("state", "")).lower() == "running"
            )
            success = sum(
                1
                for s in session_list
                if str(s.get("result", s.get("lastResult", ""))).lower() in ("success", "0")
                or (isinstance(s.get("result"), dict) and s["result"].get("result") == "Success")
            )
            warning = sum(
                1
                for s in session_list
                if str(s.get("result", s.get("lastResult", ""))).lower() in ("warning", "1")
                or (isinstance(s.get("result"), dict) and s["result"].get("result") == "Warning")
            )
            failed = sum(
                1
                for s in session_list
                if str(s.get("result", s.get("lastResult", ""))).lower() in ("failed", "2")
                or (isinstance(s.get("result"), dict) and s["result"].get("result") == "Failed")
            )

            if repos.get("_total_bytes"):
                total_space = repos["_total_bytes"]
                used_space = repos.get("_used_bytes", 0)
            else:
                total_space = sum(
                    int(r.get("capacityBytes", 0) or r.get("capacity", 0) or r.get("totalSpaceBytes", 0) or 0)
                    for r in repo_list
                )
                used_space = sum(
                    int(r.get("usedSpaceBytes", 0) or r.get("used_space_bytes", 0) or 0)
                    for r in repo_list
                )

            name = jobs.get("_server_name") or ""
            version = jobs.get("_server_version") or ""

            return {
                "success": True,
                "version": version,
                "name": name,
                "total_jobs": len(job_list),
                "running_jobs": running,
                "total_repositories": len(repo_list),
                "total_space_bytes": total_space,
                "used_space_bytes": used_space,
                "recent_sessions": len(session_list),
                "sessions_success": success,
                "sessions_warning": warning,
                "sessions_failed": failed,
            }
        except Exception as exc:
            logger.exception("Veeam summary failed")
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Jobs                                                                #
    # ------------------------------------------------------------------ #

    async def get_jobs(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:jobs")
            if result.get("success") or result.get("jobs"):
                return {
                    "success": True,
                    "jobs": result.get("jobs", []) or [],
                    "count": len(result.get("jobs", []) or []),
                    "_server_name": result.get("server_name", ""),
                    "_server_version": result.get("version", ""),
                }
            return {"success": False, "error": result.get("error"), "jobs": []}
        if self._has_ssh():
            return await self._get_jobs_from_pg()
        try:
            data = await self._get("/api/v1/jobs")
            items = _extract_items(data)
            total = (
                data.get("pagination", {}).get("total", len(items))
                if isinstance(data, dict)
                else len(items)
            )
            return {"success": True, "jobs": items, "count": total}
        except Exception as exc:
            logger.exception("Veeam get_jobs failed")
            return {"success": False, "error": str(exc), "jobs": []}

    async def _get_jobs_from_pg(self) -> dict:
        """Fallback: build job list from PostgreSQL aggregated stats."""
        stats_resp = await self.get_job_stats()
        if not stats_resp.get("success") or not stats_resp.get("jobs"):
            if self.data_source == "ssh":
                return await self._get_jobs_from_pg_fallback()
            return {"success": True, "jobs": [], "count": 0}
        jobs = []
        for j in stats_resp["jobs"]:
            last_run = None
            if j.get("last_run"):
                last_run = {
                    "endTime": j["last_run"],
                    "result": {"result": "Success"} if j.get("success_count", 0) > 0 else {"result": "Warning"},
                }
            failed = j.get("failed_count", 0)
            total = j.get("session_count", 0)
            state = "Stopped"
            if failed > 0:
                state = "Failed"
            jobs.append({
                "id": j["job_name"],
                "name": j["job_name"],
                "type": "Backup",
                "state": state,
                "enabled": True,
                "schedule": None,
                "lastRun": last_run,
                "includedObjects": {"objectsInJob": total},
                "_pg_stats": {
                    "processed_bytes": j.get("processed_bytes", 0),
                    "read_bytes": j.get("read_bytes", 0),
                    "stored_bytes": j.get("stored_bytes", 0),
                    "avg_speed": j.get("avg_speed", 0),
                    "session_count": j.get("session_count", 0),
                    "success_count": j.get("success_count", 0),
                    "warning_count": j.get("warning_count", 0),
                    "failed_count": j.get("failed_count", 0),
                },
            })
        return {"success": True, "jobs": jobs, "count": len(jobs)}

    async def _get_jobs_from_pg_fallback(self) -> dict:
        from app.plugins.installed.official_veeam.sql_queries import job_names_sql
        sql = job_names_sql(db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "jobs": [],
                "count": 0,
                "error": result.get("stderr")
                or result.get("error", "PostgreSQL query failed"),
            }
        jobs = []
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            name = line.strip()
            if not name or name.startswith("(") or name.startswith("WARNING"):
                continue
            jobs.append({
                "id": name,
                "name": name,
                "type": "Backup",
                "state": "Stopped",
                "enabled": True,
                "schedule": None,
                "lastRun": None,
                "includedObjects": {"objectsInJob": 0},
            })
        return {"success": True, "jobs": jobs, "count": len(jobs)}

    async def get_job_detail(self, job_id: str) -> dict:
        try:
            data = await self._get(f"/api/v1/jobs/{job_id}")
            return {"success": True, "job": data}
        except Exception as exc:
            logger.exception("Veeam get_job_detail failed")
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Sessions                                                            #
    # ------------------------------------------------------------------ #

    async def get_sessions(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:sessions")
            if result.get("success") or result.get("sessions"):
                return {
                    "success": True,
                    "sessions": result.get("sessions", []) or [],
                    "count": len(result.get("sessions", []) or []),
                }
            return {"success": False, "error": result.get("error"), "sessions": []}
        if self.data_source == "ssh":
            return await self._get_sessions_from_pg()
        try:
            data = await self._get("/api/v1/sessions")
            items = _extract_items(data)
            total = (
                data.get("pagination", {}).get("total", len(items))
                if isinstance(data, dict)
                else len(items)
            )
            return {"success": True, "sessions": items, "count": total}
        except Exception as exc:
            logger.exception("Veeam get_sessions failed")
            return {
                "success": False,
                "error": str(exc),
                "sessions": [],
            }

    async def _get_sessions_from_pg(self) -> dict:
        """Get sessions directly from PostgreSQL via SSH bridge."""
        stats_resp = await self.get_session_stats()
        if not stats_resp.get("success"):
            return {"success": True, "sessions": [], "count": 0}
        sessions = []
        result_map = {"0": {"result": "Success"}, "1": {"result": "Warning"}, "2": {"result": "Failed"}}
        for s in stats_resp.get("stats", []):
            sessions.append({
                "id": s["session_id"],
                "jobId": s.get("job_id", ""),
                "name": s["job_name"],
                "sessionType": "BackupJob",
                "state": "Stopped",
                "result": result_map.get(s.get("result", ""), {}),
                "creationTime": s.get("creation_time"),
                "endTime": s.get("end_time"),
                "progressPercent": 100,
            })
        return {"success": True, "sessions": sessions, "count": len(sessions)}

    # ------------------------------------------------------------------ #
    # Repositories                                                        #
    # ------------------------------------------------------------------ #

    async def get_repositories(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:repositories")
            if result.get("success") or result.get("repositories"):
                return {
                    "success": True,
                    "repositories": result.get("repositories", []) or [],
                    "count": len(result.get("repositories", []) or []),
                    "_total_bytes": 0,
                    "_used_bytes": 0,
                }
            return {"success": False, "error": result.get("error"), "repositories": []}
        try:
            data = await self._get(
                "/api/v1/backupInfrastructure/repositories"
            )
            items = _extract_items(data)
            return {
                "success": True,
                "repositories": items,
                "count": len(items),
            }
        except Exception as exc:
            logger.exception("Veeam get_repositories failed")
            return {
                "success": False,
                "error": str(exc),
                "repositories": [],
            }

    # ------------------------------------------------------------------ #
    # Managed servers                                                     #
    # ------------------------------------------------------------------ #

    async def get_managed_servers(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:managed_servers")
            if result.get("success") or result.get("servers"):
                return {
                    "success": True,
                    "servers": result.get("servers", []) or [],
                    "count": len(result.get("servers", []) or []),
                }
            return {"success": False, "error": result.get("error"), "servers": []}
        try:
            data = await self._get(
                "/api/v1/backupInfrastructure/managedServers"
            )
            items = _extract_items(data)
            return {
                "success": True,
                "servers": items,
                "count": len(items),
            }
        except Exception as exc:
            logger.exception("Veeam get_managed_servers failed")
            return {
                "success": False,
                "error": str(exc),
                "servers": [],
            }

    # ------------------------------------------------------------------ #
    # Restore points                                                      #
    # ------------------------------------------------------------------ #

    async def get_restore_points(
        self, vm_id: str | None = None
    ) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:restore_points")
            items = result.get("restore_points", []) or []
            if vm_id:
                items = [r for r in items if r.get("vmId") == vm_id]
            return {
                "success": True,
                "restore_points": items,
                "count": len(items),
            }
        try:
            data = await self._get("/api/v1/restorePoints")
            items = _extract_items(data)
            if vm_id:
                items = [
                    r for r in items if r.get("vmId") == vm_id
                ]
            return {
                "success": True,
                "restore_points": items,
                "count": len(items),
            }
        except Exception as exc:
            logger.exception("Veeam get_restore_points failed")
            return {
                "success": False,
                "error": str(exc),
                "restore_points": [],
            }

    # ------------------------------------------------------------------ #
    # License                                                             #
    # ------------------------------------------------------------------ #

    async def get_license(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:license")
            lic = result.get("license")
            if isinstance(lic, dict):
                return {"success": True, "license": lic}
            return {"success": False, "error": result.get("error", "License unavailable")}
        try:
            data = await self._get("/api/v1/license")
            return {"success": True, "license": data}
        except Exception as exc:
            logger.exception("Veeam get_license failed")
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Capacity tier                                                       #
    # ------------------------------------------------------------------ #

    async def get_capacity_tier(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:capacity_tier")
            return {
                "success": result.get("success", False),
                "object_storages": result.get("object_storages", []) or [],
                "count": result.get("count", 0),
            }
        try:
            data = await self._get(
                "/api/v1/backupInfrastructure/objectStorages"
            )
            items = _extract_items(data)
            return {
                "success": True,
                "object_storages": items,
                "count": len(items),
            }
        except Exception as exc:
            logger.exception("Veeam get_capacity_tier failed")
            return {
                "success": False,
                "error": str(exc),
                "object_storages": [],
            }

    # ------------------------------------------------------------------ #
    # Job control                                                         #
    # ------------------------------------------------------------------ #

    async def start_job(self, job_id: str) -> dict:
        if self._has_relay():
            result = await self._relay("start_job", {"job_id": job_id})
            return {
                "success": result.get("success", False),
                "message": result.get("message"),
                "error": result.get("error"),
            }
        try:
            await self._post(f"/api/v1/jobs/{job_id}/start")
            return {
                "success": True,
                "message": f"Job {job_id} started",
            }
        except Exception as exc:
            logger.exception("Veeam start_job failed")
            return {"success": False, "error": str(exc)}

    async def stop_job(self, job_id: str) -> dict:
        if self._has_relay():
            result = await self._relay("stop_job", {"job_id": job_id})
            return {
                "success": result.get("success", False),
                "message": result.get("message"),
                "error": result.get("error"),
            }
        try:
            await self._post(f"/api/v1/jobs/{job_id}/stop")
            return {
                "success": True,
                "message": f"Job {job_id} stopped",
            }
        except Exception as exc:
            logger.exception("Veeam stop_job failed")
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def get_health(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:test")
            healthy = bool(
                result.get("success")
                or result.get("rest_available")
                or result.get("db_available")
                or result.get("powershell_available")
            )
            version = result.get("version", "")
            name = result.get("name", "")
            if not version and name == "":
                jobs = await self.get_jobs()
                version = jobs.get("_server_version", "")
                name = jobs.get("_server_name", "")
            return {
                "healthy": healthy,
                "version": version,
                "name": name,
                "error": None if healthy else (result.get("error") or "Relay unavailable"),
            }
        try:
            info = await self._get("/api/v1/serverInfo")
            return {
                "healthy": True,
                "version": info.get("buildVersion", ""),
                "name": info.get("name", ""),
            }
        except Exception as exc:
            return {"healthy": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # SSH + PostgreSQL/MSSQL Bridge (relayed via agent)                   #
    # ------------------------------------------------------------------ #

    def _has_ssh(self) -> bool:
        """Check if SSH bridge is configured."""
        return bool(self.ssh_host and self.ssh_username) or self._has_relay()

    async def _run_pg_query(self, sql: str) -> dict:
        """Execute a SQL query on the Veeam database via agent+db_bridge."""
        from app.plugins.installed.official_veeam.db_bridge import run_db_query
        if not self._has_ssh():
            return {"success": False, "error": "SSH bridge not configured", "output": ""}
        return await run_db_query(
            sql=sql,
            ssh_host=self.ssh_host,
            ssh_port=self.ssh_port,
            ssh_username=self.ssh_username,
            ssh_password=self.ssh_password,
            db_type=self.db_type,
            db=self._db,
            server_id=self.server_id,
            agent_id=self.agent_id,
            target_id=self.target_id,
        )

    async def get_session_stats(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:session_stats")
            if result.get("success") or result.get("stats"):
                return {
                    "success": True,
                    "stats": result.get("stats", []) or [],
                    "ssh_available": result.get("ssh_available", True),
                    "count": len(result.get("stats", []) or []),
                    "message": result.get("message"),
                }
            return {
                "success": False,
                "stats": [],
                "ssh_available": result.get("ssh_available", False),
                "error": result.get("error"),
            }
        from app.plugins.installed.official_veeam.sql_queries import session_stats_sql
        if not self._has_ssh():
            return {
                "success": True,
                "stats": [],
                "ssh_available": False,
                "message": "SSH bridge not configured",
            }

        sql = session_stats_sql(db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "stats": [],
                "ssh_available": False,
                "error": result.get("stderr")
                or result.get("error", "PostgreSQL query failed"),
            }

        stats = []
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("(") or line.startswith("WARNING"):
                continue
            parts = line.split("|")
            if len(parts) >= 11:
                stats.append({
                    "session_id": parts[0].strip(),
                    "job_id": parts[1].strip(),
                    "job_name": parts[2].strip(),
                    "state": parts[3].strip(),
                    "creation_time": parts[4].strip(),
                    "end_time": parts[5].strip(),
                    "result": parts[6].strip(),
                    "processed_bytes": int(parts[8].strip() or 0),
                    "read_bytes": int(parts[9].strip() or 0),
                    "transferred_bytes": int(parts[10].strip() or 0),
                })

        return {
            "success": True,
            "stats": stats,
            "ssh_available": True,
            "count": len(stats),
        }

    async def get_job_stats(self) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:job_stats")
            if result.get("success") or result.get("jobs"):
                return {
                    "success": True,
                    "jobs": result.get("jobs", []) or [],
                    "ssh_available": result.get("ssh_available", True),
                    "count": len(result.get("jobs", []) or []),
                    "message": result.get("message"),
                }
            return {
                "success": False,
                "jobs": [],
                "ssh_available": result.get("ssh_available", False),
                "error": result.get("error"),
            }
        from app.plugins.installed.official_veeam.sql_queries import job_stats_sql
        if not self._has_ssh():
            return {
                "success": True,
                "jobs": [],
                "ssh_available": False,
                "message": "SSH bridge not configured",
            }

        sql = job_stats_sql(db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "jobs": [],
                "ssh_available": False,
                "error": result.get("stderr")
                or result.get("error", "PostgreSQL query failed"),
            }

        jobs = []
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("(") or line.startswith("WARNING"):
                continue
            parts = line.split("|")
            if len(parts) >= 11:
                jobs.append({
                    "job_name": parts[0].strip(),
                    "session_count": int(parts[1].strip() or 0),
                    "total_bytes": int(parts[2].strip() or 0),
                    "processed_bytes": int(parts[3].strip() or 0),
                    "read_bytes": int(parts[4].strip() or 0),
                    "stored_bytes": int(parts[5].strip() or 0),
                    "avg_speed": int(float(parts[6].strip() or 0)),
                    "last_run": parts[7].strip(),
                    "success_count": int(parts[8].strip() or 0),
                    "warning_count": int(parts[9].strip() or 0),
                    "failed_count": int(parts[10].strip() or 0),
                })

        return {
            "success": True,
            "jobs": jobs,
            "ssh_available": True,
            "count": len(jobs),
        }

    async def get_job_stats_daily(self, days: int = 7) -> dict:
        if self._has_relay():
            result = await self._relay("veeam:job_stats_daily", {"days": int(days)})
            if result.get("success") or result.get("jobs"):
                return {
                    "success": True,
                    "jobs": result.get("jobs", []) or [],
                    "dates": result.get("dates", []) or [],
                    "ssh_available": result.get("ssh_available", True),
                    "count": len(result.get("jobs", []) or []),
                    "message": result.get("message"),
                }
            return {
                "success": False,
                "jobs": [],
                "dates": [],
                "ssh_available": result.get("ssh_available", False),
                "error": result.get("error"),
            }
        from app.plugins.installed.official_veeam.sql_queries import job_stats_daily_sql
        if not self._has_ssh():
            return {
                "success": True,
                "jobs": [],
                "dates": [],
                "ssh_available": False,
                "message": "SSH bridge not configured",
            }

        sql = job_stats_daily_sql(days=days, db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "jobs": [],
                "dates": [],
                "ssh_available": False,
                "error": result.get("stderr")
                or result.get("error", "PostgreSQL query failed"),
            }

        job_map: dict[str, dict[str, dict]] = {}
        dates_set: set[str] = set()
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("(") or line.startswith("WARNING"):
                continue
            parts = line.split("|")
            if len(parts) >= 9:
                job_name = parts[0].strip()
                run_date = parts[1].strip()
                processed = int(parts[2].strip() or 0)
                read_bytes = int(parts[3].strip() or 0)
                stored = int(parts[4].strip() or 0)
                session_count = int(parts[5].strip() or 0)
                success = int(parts[6].strip() or 0)
                warning = int(parts[7].strip() or 0)
                failed = int(parts[8].strip() or 0)

                if failed > 0:
                    result_status = "Failed"
                elif warning > 0:
                    result_status = "Warning"
                else:
                    result_status = "Success"

                dates_set.add(run_date)
                if job_name not in job_map:
                    job_map[job_name] = {}
                job_map[job_name][run_date] = {
                    "processed_bytes": processed,
                    "read_bytes": read_bytes,
                    "stored_bytes": stored,
                    "session_count": session_count,
                    "success_count": success,
                    "warning_count": warning,
                    "failed_count": failed,
                    "result": result_status,
                }

        jobs = []
        for job_name, daily in job_map.items():
            jobs.append({
                "job_name": job_name,
                "daily": daily,
            })

        dates = sorted(dates_set, reverse=True)

        return {
            "success": True,
            "jobs": jobs,
            "dates": dates,
            "ssh_available": True,
            "count": len(jobs),
        }
