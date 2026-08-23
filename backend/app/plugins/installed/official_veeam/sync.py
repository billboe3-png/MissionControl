"""
Veeam Plugin Sync

Background synchronization classes that pull data from Veeam B&R
and write to local cache tables.
"""

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.plugins.installed.official_veeam.models import (
    VeeamBackupServer,
    VeeamJob,
    VeeamLicense,
    VeeamRepository,
    VeeamRestorePoint,
)

logger = logging.getLogger("plugin.veeam.sync")


def _extract_items(data: Any) -> list:
    """Extract items from Veeam paginated response."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []


class ServerSync:
    """Synchronize server info from Veeam REST API to local cache."""

    def sync(self, session: Session, client: Any, server_id: int) -> dict[str, int]:
        result = client.get_summary_sync()
        server_row = session.get(VeeamBackupServer, server_id)
        if server_row:
            server_row.version = result.get("version", "")
            server_row.status = "healthy" if result.get("success") else "error"
            server_row.last_sync_at = datetime.now(UTC)
            server_row.last_error = result.get("error")
        session.commit()
        return {"synced": 1}


class RepositorySync:
    """Synchronize repository inventory from Veeam to local cache."""

    def sync(self, session: Session, client: Any, server_id: int) -> dict[str, int]:
        result = client.get_repositories_sync()
        items = _extract_items(result.get("repositories", []))
        synced = 0

        for r in items:
            veeam_id = str(r.get("id", r.get("repositoryId", "")))
            if not veeam_id:
                continue

            total = int(r.get("capacity", r.get("totalSpaceBytes", 0)) or 0)
            free = int(r.get("freeSpace", r.get("freeSpaceBytes", 0)) or 0)
            used = total - free if total > 0 else 0
            name = r.get("name", r.get("displayName", "Unknown"))
            path = r.get("path", "")
            repo_type = r.get("type", r.get("repositoryType", "local"))
            status = r.get("status", "online")
            desc = r.get("description", "")
            immutable = r.get("isImmutabilityEnabled", False)

            stmt = select(VeeamRepository).where(
                VeeamRepository.server_id == server_id,
                VeeamRepository.veeam_id == veeam_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.name = name
                existing.path = path
                existing.repo_type = repo_type
                existing.status = status
                existing.total_space_bytes = total
                existing.free_space_bytes = free
                existing.used_space_bytes = used
                existing.is_immutability_enabled = immutable
                existing.description = desc
                existing.last_sync_at = datetime.now(UTC)
            else:
                session.add(VeeamRepository(
                    server_id=server_id,
                    veeam_id=veeam_id,
                    name=name,
                    path=path,
                    repo_type=repo_type,
                    status=status,
                    total_space_bytes=total,
                    free_space_bytes=free,
                    used_space_bytes=used,
                    is_immutability_enabled=immutable,
                    description=desc,
                    last_sync_at=datetime.now(UTC),
                ))
            synced += 1

        session.commit()
        logger.info("Repository sync: %d repos synced", synced)
        return {"synced": synced}


class JobSync:
    """Synchronize backup jobs from Veeam to local cache."""

    JOB_TYPE_MAP: ClassVar[dict[str, str]] = {
        "backup": "backup",
        "replica": "replication",
        "copy": "backup_copy",
        "agent": "agent",
        "nas": "nas",
        "tape": "tape",
    }

    def sync(self, session: Session, client: Any, server_id: int) -> dict[str, int]:
        result = client.get_jobs_sync()
        items = _extract_items(result.get("jobs", []))
        synced = 0

        for j in items:
            veeam_id = str(j.get("id", j.get("jobId", "")))
            if not veeam_id:
                continue

            name = j.get("name", j.get("displayName", "Unknown"))
            job_type_raw = j.get("type", j.get("jobType", "backup"))
            job_type = self.JOB_TYPE_MAP.get(str(job_type_raw).lower(), "backup")
            is_enabled = j.get("isEnabled", j.get("enabled", True))
            status = j.get("status", "unknown")
            last_result = j.get("lastResult", j.get("result", None))
            next_run = j.get("nextRun", j.get("nextRunTime", None))

            stmt = select(VeeamJob).where(
                VeeamJob.server_id == server_id,
                VeeamJob.veeam_id == veeam_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.name = name
                existing.job_type = job_type
                existing.status = status
                existing.is_enabled = is_enabled
                existing.last_result = last_result
                existing.next_run_at = str(next_run) if next_run else None
            else:
                session.add(VeeamJob(
                    server_id=server_id,
                    veeam_id=veeam_id,
                    name=name,
                    job_type=job_type,
                    status=status,
                    is_enabled=is_enabled,
                    last_result=last_result,
                    next_run_at=str(next_run) if next_run else None,
                ))
            synced += 1

        session.commit()
        logger.info("Job sync: %d jobs synced", synced)
        return {"synced": synced, "total": synced}


class RestorePointSync:
    """Synchronize restore points from Veeam to local cache."""

    def sync(
        self, session: Session, client: Any, server_id: int, limit: int = 500,
    ) -> dict[str, int]:
        result = client.get_restore_points_sync()
        items = _extract_items(result.get("restorePoints", []))
        synced = 0

        for rp in items[:limit]:
            veeam_id = str(rp.get("id", rp.get("restorePointId", "")))
            if not veeam_id:
                continue

            name = rp.get("name", rp.get("displayName", "Unknown"))
            vm_name = rp.get("vmName", rp.get("name", ""))
            vm_id = str(rp.get("vmId", ""))
            repo_id = str(rp.get("repositoryId", ""))
            repo_name = rp.get("repositoryName", "")
            rp_type = rp.get("type", rp.get("restorePointType", ""))
            created_str = rp.get("createdTime", rp.get("creationTime", ""))
            point_size = int(rp.get("pointSize", rp.get("pointSizeBytes", 0)) or 0)

            created_at = None
            if created_str:
                with contextlib.suppress(ValueError, TypeError):
                    created_at = datetime.fromisoformat(
                        str(created_str).replace("Z", "+00:00")
                    )

            stmt = select(VeeamRestorePoint).where(
                VeeamRestorePoint.server_id == server_id,
                VeeamRestorePoint.veeam_id == veeam_id,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if not existing:
                session.add(VeeamRestorePoint(
                    server_id=server_id,
                    veeam_id=veeam_id,
                    name=name,
                    vm_name=vm_name,
                    vm_id=vm_id or None,
                    repository_id=repo_id or None,
                    repository_name=repo_name or None,
                    restore_point_type=rp_type or None,
                    created_at_ts=created_at,
                    point_size_bytes=point_size,
                ))
            synced += 1

        session.commit()
        logger.info("Restore point sync: %d points synced", synced)
        return {"synced": synced}


class LicenseSync:
    """Synchronize license information from Veeam to local cache."""

    def sync(self, session: Session, client: Any, server_id: int) -> dict[str, int]:
        result = client.get_license_sync()
        lic = result.get("license", result)

        stmt = select(VeeamLicense).where(VeeamLicense.server_id == server_id)
        existing = session.execute(stmt).scalar_one_or_none()

        edition = lic.get("edition", lic.get("licenseEdition", ""))
        expiration = lic.get("expirationDate", lic.get("expiration", ""))
        lic_type = lic.get("type", lic.get("licenseType", ""))
        used = int(lic.get("usedLicenses", lic.get("used", 0)) or 0)
        total = int(lic.get("totalLicenses", lic.get("total", 0)) or 0)

        if existing:
            existing.edition = edition
            existing.expiration_date = str(expiration) if expiration else None
            existing.license_type = lic_type
            existing.used_licenses = used
            existing.total_licenses = total
            existing.synced_at = datetime.now(UTC)
        else:
            session.add(VeeamLicense(
                server_id=server_id,
                edition=edition,
                expiration_date=str(expiration) if expiration else None,
                license_type=lic_type,
                used_licenses=used,
                total_licenses=total,
            ))

        session.commit()
        logger.info("License sync: edition=%s", edition)
        return {"synced": 1}
