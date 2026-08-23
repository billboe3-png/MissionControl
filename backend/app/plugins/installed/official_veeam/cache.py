"""
Veeam Plugin Cache

Provides convenient read access to cached Veeam data.
All queries use synchronous SQLAlchemy sessions.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.plugins.installed.official_veeam.models import (
    VeeamBackupServer,
    VeeamJob,
    VeeamLicense,
    VeeamRepository,
    VeeamRestorePoint,
)

logger = logging.getLogger("plugin.veeam.cache")


def _server_to_dict(s: VeeamBackupServer) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "edition": s.edition,
        "data_source": s.data_source,
        "db_type": s.db_type,
        "column_case": s.column_case,
        "agent_id": s.agent_id,
        "target_id": s.target_id,
        "rest_url": s.rest_url,
        "enabled": s.enabled,
        "status": s.status,
        "version": s.version,
        "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
        "last_error": s.last_error,
        "last_diagnostic": _parse_diagnostic(s.last_diagnostic),
    }


def _parse_diagnostic(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        import json
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def _repo_to_dict(r: VeeamRepository) -> dict[str, Any]:
    return {
        "id": r.id,
        "server_id": r.server_id,
        "veeam_id": r.veeam_id,
        "name": r.name,
        "path": r.path,
        "repo_type": r.repo_type,
        "status": r.status,
        "total_space_bytes": r.total_space_bytes,
        "free_space_bytes": r.free_space_bytes,
        "used_space_bytes": r.used_space_bytes,
        "is_immutability_enabled": r.is_immutability_enabled,
        "description": r.description,
    }


def _job_to_dict(j: VeeamJob) -> dict[str, Any]:
    return {
        "id": j.id,
        "server_id": j.server_id,
        "veeam_id": j.veeam_id,
        "name": j.name,
        "job_type": j.job_type,
        "status": j.status,
        "is_enabled": j.is_enabled,
        "last_result": j.last_result,
        "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
        "next_run_at": j.next_run_at,
    }


def _rp_to_dict(rp: VeeamRestorePoint) -> dict[str, Any]:
    return {
        "id": rp.id,
        "server_id": rp.server_id,
        "veeam_id": rp.veeam_id,
        "name": rp.name,
        "vm_name": rp.vm_name,
        "repository_name": rp.repository_name,
        "restore_point_type": rp.restore_point_type,
        "created_at": rp.created_at_ts.isoformat() if rp.created_at_ts else None,
        "point_size_bytes": rp.point_size_bytes,
    }


def _lic_to_dict(lic: VeeamLicense) -> dict[str, Any]:
    return {
        "server_id": lic.server_id,
        "edition": lic.edition,
        "expiration_date": lic.expiration_date,
        "license_type": lic.license_type,
        "used_licenses": lic.used_licenses,
        "total_licenses": lic.total_licenses,
    }


class CacheManager:
    """Read-only access to cached Veeam data."""

    def get_servers(self, db: Session) -> list[dict[str, Any]]:
        rows = db.execute(
            select(VeeamBackupServer).order_by(VeeamBackupServer.name)
        ).scalars().all()
        return [_server_to_dict(r) for r in rows]

    def get_repositories(
        self, db: Session, server_id: int | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(VeeamRepository)
        if server_id:
            stmt = stmt.where(VeeamRepository.server_id == server_id)
        rows = db.execute(stmt.order_by(VeeamRepository.name)).scalars().all()
        return [_repo_to_dict(r) for r in rows]

    def get_jobs(
        self, db: Session, server_id: int | None = None, job_type: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(VeeamJob)
        if server_id:
            stmt = stmt.where(VeeamJob.server_id == server_id)
        if job_type:
            stmt = stmt.where(VeeamJob.job_type == job_type)
        rows = db.execute(stmt.order_by(VeeamJob.name)).scalars().all()
        return [_job_to_dict(r) for r in rows]

    def get_restore_points(
        self, db: Session, server_id: int | None = None, vm_name: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(VeeamRestorePoint)
        if server_id:
            stmt = stmt.where(VeeamRestorePoint.server_id == server_id)
        if vm_name:
            stmt = stmt.where(VeeamRestorePoint.vm_name.ilike(f"%{vm_name}%"))
        rows = db.execute(
            stmt.order_by(VeeamRestorePoint.created_at_ts.desc())
        ).scalars().all()
        return [_rp_to_dict(r) for r in rows]

    def get_license(self, db: Session) -> list[dict[str, Any]]:
        rows = db.execute(select(VeeamLicense)).scalars().all()
        return [_lic_to_dict(r) for r in rows]

    def get_summary(self, db: Session) -> dict[str, Any]:
        server_count = (db.execute(
            select(func.count(VeeamBackupServer.id))
        ).scalar()) or 0

        repo_count = (db.execute(
            select(func.count(VeeamRepository.id))
        ).scalar()) or 0

        total_space = (db.execute(
            select(func.coalesce(func.sum(VeeamRepository.total_space_bytes), 0))
        ).scalar()) or 0

        free_space = (db.execute(
            select(func.coalesce(func.sum(VeeamRepository.free_space_bytes), 0))
        ).scalar()) or 0

        job_count = (db.execute(
            select(func.count(VeeamJob.id))
        ).scalar()) or 0

        jobs_enabled = (db.execute(
            select(func.count(VeeamJob.id)).where(VeeamJob.is_enabled.is_(True))
        ).scalar()) or 0

        rp_count = (db.execute(
            select(func.count(VeeamRestorePoint.id))
        ).scalar()) or 0

        immutable_count = (db.execute(
            select(func.count(VeeamRepository.id)).where(
                VeeamRepository.is_immutability_enabled.is_(True)
            )
        ).scalar()) or 0

        servers = self.get_servers(db)
        healthy = sum(1 for s in servers if s["status"] == "healthy")

        return {
            "server_count": server_count,
            "servers_healthy": healthy,
            "repository_count": repo_count,
            "total_space_bytes": int(total_space),
            "free_space_bytes": int(free_space),
            "used_space_bytes": int(total_space) - int(free_space),
            "job_count": job_count,
            "jobs_enabled": jobs_enabled,
            "restore_point_count": rp_count,
            "immutable_repositories": immutable_count,
        }

    def get_repo_health(self, db: Session) -> list[dict[str, Any]]:
        """Return repository health data with capacity percentages."""
        repos = self.get_repositories(db)
        for r in repos:
            total = r["total_space_bytes"]
            free = r["free_space_bytes"]
            used_pct = ((total - free) / total * 100) if total > 0 else 0
            r["used_pct"] = round(used_pct, 1)
            r["free_pct"] = round(100 - used_pct, 1)
        return repos

    def get_jobs_by_status(self, db: Session) -> dict[str, int]:
        """Count jobs grouped by status."""
        rows = db.execute(
            select(VeeamJob.status, func.count(VeeamJob.id))
            .group_by(VeeamJob.status)
        ).all()
        return {row[0]: row[1] for row in rows}

    def get_jobs_by_type(self, db: Session) -> dict[str, int]:
        """Count jobs grouped by type."""
        rows = db.execute(
            select(VeeamJob.job_type, func.count(VeeamJob.id))
            .group_by(VeeamJob.job_type)
        ).all()
        return {row[0]: row[1] for row in rows}

    def get_last_sync(self, db: Session) -> str | None:
        """Return the most recent sync timestamp across all servers."""
        latest = db.execute(
            select(func.max(VeeamBackupServer.last_sync_at))
        ).scalar()
        return latest.isoformat() if latest else None


cache_manager = CacheManager()
