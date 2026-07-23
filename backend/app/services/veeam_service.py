"""
Mission Control Veeam B&R Service

Business logic for Veeam Backup & Replication operations.
Delegates to Veeam provider(s) for all data access.
Supports multiple concurrent Veeam server profiles.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VeeamService:
    """Thin service layer over one or more Veeam B&R providers."""

    def _get_providers(
        self, db: Session | None = None
    ) -> list[tuple[str, Any]]:
        from app.providers.veeam.provider_factory import get_all_veeam_providers

        return get_all_veeam_providers(db)

    async def get_summary(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_summary()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_summary()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get summary from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        total: dict[str, Any] = {
            "success": True,
            "servers": [],
            "total_jobs": 0,
            "running_jobs": 0,
            "total_repositories": 0,
            "total_space_bytes": 0,
            "used_space_bytes": 0,
            "recent_sessions": 0,
            "sessions_success": 0,
            "sessions_warning": 0,
            "sessions_failed": 0,
        }
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            elif data.get("success"):
                total["servers"].append({"name": name, **data})
                total["total_jobs"] += data.get("total_jobs", 0)
                total["running_jobs"] += data.get("running_jobs", 0)
                total["total_repositories"] += data.get("total_repositories", 0)
                total["total_space_bytes"] += data.get("total_space_bytes", 0)
                total["used_space_bytes"] += data.get("used_space_bytes", 0)
                total["recent_sessions"] += data.get("recent_sessions", 0)
                total["sessions_success"] += data.get("sessions_success", 0)
                total["sessions_warning"] += data.get("sessions_warning", 0)
                total["sessions_failed"] += data.get("sessions_failed", 0)
            else:
                errors.append(f"{name}: {data.get('error', 'unknown')}")
        if errors:
            total["error"] = "; ".join(errors)
        return total

    async def test_connection(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.test_connection()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                r = await p.test_connection()
                r["server_name"] = name
                return name, r, None
            except Exception as exc:
                return name, {"connected": False, "server_name": name, "error": str(exc)}, None

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        merged = [data for _, data, _ in results]
        connected = any(r.get("connected") for r in merged)
        return {"connected": connected, "results": merged}

    async def get_health(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_health()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                h = await p.get_health()
                h["server_name"] = name
                return name, h, None
            except Exception as exc:
                return name, {"healthy": False, "server_name": name, "error": str(exc)}, None

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        merged = [data for _, data, _ in results]
        healthy = all(r.get("healthy") for r in merged)
        return {"healthy": healthy, "results": merged}

    async def get_jobs(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_jobs()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_jobs()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get jobs from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_jobs: list[dict] = []
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                for job in data.get("jobs", []):
                    job["server_name"] = name
                all_jobs.extend(data.get("jobs", []))
        return {
            "success": True,
            "jobs": all_jobs,
            "server_names": [n for n, _ in providers],
            "count": len(all_jobs),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_job_detail(self, job_id: str, db: Session | None = None) -> dict:
        return await self._get_providers(db)[0][1].get_job_detail(job_id)

    async def start_job(self, job_id: str, db: Session | None = None) -> dict:
        return await self._get_providers(db)[0][1].start_job(job_id)

    async def stop_job(self, job_id: str, db: Session | None = None) -> dict:
        return await self._get_providers(db)[0][1].stop_job(job_id)

    async def get_sessions(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_sessions()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_sessions()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get sessions from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_sessions: list[dict] = []
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                for s in data.get("sessions", []):
                    s["server_name"] = name
                all_sessions.extend(data.get("sessions", []))
        all_sessions.sort(key=lambda s: s.get("creationTime") or s.get("creation_time") or "", reverse=True)
        return {
            "success": True,
            "sessions": all_sessions,
            "server_names": [n for n, _ in providers],
            "count": len(all_sessions),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_repositories(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_repositories()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_repositories()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get repos from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_repos: list[dict] = []
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                for r in data.get("repositories", []):
                    r["server_name"] = name
                all_repos.extend(data.get("repositories", []))
        return {
            "success": True,
            "repositories": all_repos,
            "count": len(all_repos),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_managed_servers(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_managed_servers()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_managed_servers()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get managed servers from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_servers: list[dict] = []
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                for s in data.get("servers", []):
                    s["server_name"] = name
                all_servers.extend(data.get("servers", []))
        return {
            "success": True,
            "servers": all_servers,
            "count": len(all_servers),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_restore_points(
        self, vm_id: str | None = None, db: Session | None = None
    ) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_restore_points(vm_id)

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_restore_points(vm_id)
                return name, data, None
            except Exception as exc:
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_rps: list[dict] = []
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                for rp in data.get("restore_points", []):
                    rp["server_name"] = name
                all_rps.extend(data.get("restore_points", []))
        return {
            "success": True,
            "restore_points": all_rps,
            "count": len(all_rps),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_license(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_license()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_license()
                data["server_name"] = name
                return name, data, None
            except Exception:
                return name, {}, None

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        licenses = [data for _, data, err in results if not err]
        return {"success": True, "licenses": licenses}

    async def get_capacity_tier(self, db: Session | None = None) -> dict:
        return await self._get_providers(db)[0][1].get_capacity_tier()

    async def get_session_stats(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_session_stats()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_session_stats()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get session stats from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_stats: list[dict] = []
        ssh_available = False
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                if data.get("ssh_available"):
                    ssh_available = True
                for s in data.get("stats", []):
                    s["server_name"] = name
                all_stats.extend(data.get("stats", []))
        return {
            "success": True,
            "stats": all_stats,
            "server_names": [n for n, _ in providers],
            "ssh_available": ssh_available,
            "count": len(all_stats),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_job_stats(self, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_job_stats()

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_job_stats()
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get job stats from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_jobs: list[dict] = []
        ssh_available = False
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                if data.get("ssh_available"):
                    ssh_available = True
                for j in data.get("jobs", []):
                    j["server_name"] = name
                all_jobs.extend(data.get("jobs", []))
        return {
            "success": True,
            "jobs": all_jobs,
            "server_names": [n for n, _ in providers],
            "ssh_available": ssh_available,
            "count": len(all_jobs),
            "error": "; ".join(errors) if errors else None,
        }

    async def get_job_stats_daily(self, days: int = 7, db: Session | None = None) -> dict:
        providers = self._get_providers(db)
        if len(providers) == 1:
            name, p = providers[0]
            return await p.get_job_stats_daily(days=days)

        async def _fetch(name: str, p: Any) -> tuple[str, dict, str | None]:
            try:
                data = await p.get_job_stats_daily(days=days)
                return name, data, None
            except Exception as exc:
                logger.exception("Failed to get job stats daily from %s", name)
                return name, {}, str(exc)

        results = await asyncio.gather(*[_fetch(n, p) for n, p in providers])
        all_job_rows: list[dict] = []
        all_dates: set[str] = set()
        ssh_available = False
        errors = []
        for name, data, err in results:
            if err:
                errors.append(f"{name}: {err}")
            else:
                if data.get("ssh_available"):
                    ssh_available = True
                for row in data.get("jobs", []):
                    row["server_name"] = name
                    all_job_rows.append(row)
                all_dates.update(data.get("dates", []))
        sorted_dates = sorted(all_dates)
        return {
            "success": True,
            "jobs": all_job_rows,
            "dates": sorted_dates,
            "server_names": [n for n, _ in providers],
            "ssh_available": ssh_available,
            "count": len(all_job_rows),
            "error": "; ".join(errors) if errors else None,
        }


veeam_service = VeeamService()
