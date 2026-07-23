"""
Mission Control Veeam B&R Router

API endpoints for Veeam Backup & Replication operations.
Configuration comes from IntegrationProfile — never from config.py.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.veeam import (
    VeeamCapacityTierResponse,
    VeeamConnectionTestResponse,
    VeeamHealthResponse,
    VeeamJobActionResponse,
    VeeamJobDetailResponse,
    VeeamJobListResponse,
    VeeamJobStatsDailyResponse,
    VeeamJobStatsResponse,
    VeeamLicenseResponse,
    VeeamManagedServerListResponse,
    VeeamRepositoryListResponse,
    VeeamRestorePointListResponse,
    VeeamSessionListResponse,
    VeeamSessionStatsResponse,
    VeeamSummaryResponse,
)
from app.services.veeam_service import veeam_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/veeam",
    tags=["veeam"],
    dependencies=[Depends(get_current_user)],
)


# ------------------------------------------------------------------ #
# Overview & Connection                                               #
# ------------------------------------------------------------------ #


@router.get("/overview", response_model=VeeamSummaryResponse)
async def get_veeam_overview(
    db: Session = Depends(get_db),
) -> VeeamSummaryResponse:
    """Get Veeam B&R overview."""
    data = await veeam_service.get_summary(db)
    return VeeamSummaryResponse(**data)


@router.get("/test", response_model=VeeamConnectionTestResponse)
async def test_veeam_connection(
    db: Session = Depends(get_db),
) -> VeeamConnectionTestResponse:
    """Test connectivity to Veeam B&R server."""
    data = await veeam_service.test_connection(db)
    return VeeamConnectionTestResponse(**data)


@router.get("/health", response_model=VeeamHealthResponse)
async def get_veeam_health(
    db: Session = Depends(get_db),
) -> VeeamHealthResponse:
    """Get Veeam B&R health status."""
    data = await veeam_service.get_health(db)
    return VeeamHealthResponse(**data)


# ------------------------------------------------------------------ #
# Jobs                                                                #
# ------------------------------------------------------------------ #


@router.get("/jobs", response_model=VeeamJobListResponse)
async def list_jobs(
    db: Session = Depends(get_db),
) -> VeeamJobListResponse:
    """List all backup/replication jobs."""
    data = await veeam_service.get_jobs(db)
    return VeeamJobListResponse(**data)


@router.get("/jobs/stats", response_model=VeeamJobStatsResponse)
async def get_job_stats(
    db: Session = Depends(get_db),
) -> VeeamJobStatsResponse:
    """Get aggregated transfer statistics per job via SSH+PostgreSQL bridge."""
    data = await veeam_service.get_job_stats(db)
    return VeeamJobStatsResponse(**data)


@router.get("/jobs/stats/daily", response_model=VeeamJobStatsDailyResponse)
async def get_job_stats_daily(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> VeeamJobStatsDailyResponse:
    """Get per-job per-day transfer statistics via SSH+PostgreSQL bridge."""
    data = await veeam_service.get_job_stats_daily(days=days, db=db)
    return VeeamJobStatsDailyResponse(**data)


@router.get("/jobs/{job_id}", response_model=VeeamJobDetailResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> VeeamJobDetailResponse:
    """Get detailed information for a single job."""
    data = await veeam_service.get_job_detail(job_id, db)
    return VeeamJobDetailResponse(**data)


@router.post("/jobs/{job_id}/start", response_model=VeeamJobActionResponse)
async def start_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> VeeamJobActionResponse:
    """Start a backup job."""
    data = await veeam_service.start_job(job_id, db)
    return VeeamJobActionResponse(**data)


@router.post("/jobs/{job_id}/stop", response_model=VeeamJobActionResponse)
async def stop_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> VeeamJobActionResponse:
    """Stop a running backup job."""
    data = await veeam_service.stop_job(job_id, db)
    return VeeamJobActionResponse(**data)


# ------------------------------------------------------------------ #
# Sessions                                                            #
# ------------------------------------------------------------------ #


@router.get("/sessions", response_model=VeeamSessionListResponse)
async def list_sessions(
    db: Session = Depends(get_db),
) -> VeeamSessionListResponse:
    """List recent backup sessions."""
    data = await veeam_service.get_sessions(db)
    return VeeamSessionListResponse(**data)


@router.get("/sessions/stats", response_model=VeeamSessionStatsResponse)
async def get_session_stats(
    db: Session = Depends(get_db),
) -> VeeamSessionStatsResponse:
    """Get backup session transfer statistics via SSH+PowerShell bridge."""
    data = await veeam_service.get_session_stats(db)
    return VeeamSessionStatsResponse(**data)


# ------------------------------------------------------------------ #
# Repositories                                                        #
# ------------------------------------------------------------------ #


@router.get("/repositories", response_model=VeeamRepositoryListResponse)
async def list_repositories(
    db: Session = Depends(get_db),
) -> VeeamRepositoryListResponse:
    """List backup repositories."""
    data = await veeam_service.get_repositories(db)
    return VeeamRepositoryListResponse(**data)


# ------------------------------------------------------------------ #
# Managed servers                                                     #
# ------------------------------------------------------------------ #


@router.get("/servers", response_model=VeeamManagedServerListResponse)
async def list_managed_servers(
    db: Session = Depends(get_db),
) -> VeeamManagedServerListResponse:
    """List managed servers (hypervisors, Windows/Linux)."""
    data = await veeam_service.get_managed_servers(db)
    return VeeamManagedServerListResponse(**data)


# ------------------------------------------------------------------ #
# Restore points                                                      #
# ------------------------------------------------------------------ #


@router.get("/restore-points", response_model=VeeamRestorePointListResponse)
async def list_restore_points(
    vm_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> VeeamRestorePointListResponse:
    """List restore points, optionally filtered by VM."""
    data = await veeam_service.get_restore_points(vm_id, db)
    return VeeamRestorePointListResponse(**data)


# ------------------------------------------------------------------ #
# License                                                             #
# ------------------------------------------------------------------ #


@router.get("/license", response_model=VeeamLicenseResponse)
async def get_license(
    db: Session = Depends(get_db),
) -> VeeamLicenseResponse:
    """Get Veeam license information."""
    data = await veeam_service.get_license(db)
    return VeeamLicenseResponse(**data)


# ------------------------------------------------------------------ #
# Capacity tier                                                       #
# ------------------------------------------------------------------ #


@router.get("/capacity-tier", response_model=VeeamCapacityTierResponse)
async def get_capacity_tier(
    db: Session = Depends(get_db),
) -> VeeamCapacityTierResponse:
    """Get capacity tier (object storage) status."""
    data = await veeam_service.get_capacity_tier(db)
    return VeeamCapacityTierResponse(**data)
