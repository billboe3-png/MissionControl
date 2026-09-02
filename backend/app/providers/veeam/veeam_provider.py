"""
Veeam B&R REST Provider -- Production

Communicates with Veeam Backup & Replication REST API (v1).
Authenticates via OAuth2 client credentials flow.

Includes optional SSH+PostgreSQL bridge for data that the REST API
does not expose (e.g. session transfer statistics).
"""

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.providers.veeam.base_provider import VeeamProvider

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
API_VERSION = "1.3-rev1"

PG_PSQL_PATH = "C:\\Program Files\\PostgreSQL\\15\\bin\\psql.exe"
PG_DB_NAME = "VeeamBackup"
PG_SSH_TEMP_DIR = "C:\\temp"


def _extract_items(data: Any) -> list:
    """Extract items from Veeam paginated response."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


class VeeamRESTProvider:
    """Veeam B&R REST API provider."""

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

    # ------------------------------------------------------------------ #
    # HTTP helpers                                                        #
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
            info = await self._get("/api/v1/serverInfo")

            job_list: list = []
            job_pagination: dict = {}
            try:
                jobs_resp = await self._get("/api/v1/jobs")
                job_list = _extract_items(jobs_resp)
                job_pagination = (
                    jobs_resp.get("pagination", {}) if isinstance(jobs_resp, dict) else {}
                )
            except Exception:
                logger.warning("Veeam jobs endpoint unavailable for summary")

            sessions: list = []
            try:
                sessions_resp = await self._get("/api/v1/sessions")
                sessions = _extract_items(sessions_resp)
            except Exception:
                logger.warning("Veeam sessions endpoint unavailable for summary")

            repo_list: list = []
            try:
                repos_resp = await self._get(
                    "/api/v1/backupInfrastructure/repositories"
                )
                repo_list = _extract_items(repos_resp)
            except Exception:
                logger.warning("Veeam repos endpoint unavailable for summary")

            running = sum(
                1 for j in job_list if j.get("state") == "Running"
            )
            success = sum(
                1
                for s in sessions
                if isinstance(s.get("result"), dict)
                and s["result"].get("result") == "Success"
            )
            warning = sum(
                1
                for s in sessions
                if isinstance(s.get("result"), dict)
                and s["result"].get("result") == "Warning"
            )
            failed = sum(
                1
                for s in sessions
                if isinstance(s.get("result"), dict)
                and s["result"].get("result") == "Failed"
            )

            total_space = 0
            used_space = 0
            for r in repo_list:
                total_space += r.get("capacityBytes", 0) or r.get(
                    "repository", {}
                ).get("capacityBytes", 0)
                used_space += r.get("usedSpaceBytes", 0) or r.get(
                    "repository", {}
                ).get("usedSpaceBytes", 0)

            return {
                "success": True,
                "version": info.get("buildVersion", ""),
                "name": info.get("name", ""),
                "total_jobs": job_pagination.get("total", len(job_list)),
                "running_jobs": running,
                "total_repositories": len(repo_list),
                "total_space_bytes": total_space,
                "used_space_bytes": used_space,
                "recent_sessions": len(sessions),
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
        from app.providers.veeam.sql_queries import job_names_sql
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
    # SSH + PostgreSQL/MSSQL Bridge                                       #
    # ------------------------------------------------------------------ #

    def _has_ssh(self) -> bool:
        """Check if SSH bridge is configured."""
        return bool(self.ssh_host and self.ssh_username)

    async def _run_pg_query(self, sql: str) -> dict:
        """Execute a SQL query on the Veeam database via SSH+db_bridge."""
        from app.providers.veeam.db_bridge import run_db_query
        if not self._has_ssh():
            return {"success": False, "error": "SSH bridge not configured", "output": ""}
        return await run_db_query(
            sql=sql,
            ssh_host=self.ssh_host,
            ssh_port=self.ssh_port,
            ssh_username=self.ssh_username,
            ssh_password=self.ssh_password,
            db_type=self.db_type,
        )

    async def get_session_stats(self) -> dict:
        from app.providers.veeam.sql_queries import session_stats_sql
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
        from app.providers.veeam.sql_queries import job_stats_sql
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
        from app.providers.veeam.sql_queries import job_stats_daily_sql
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