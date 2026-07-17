"""
Mission Control Site Router

API endpoints for managing sites.
Sprint 2.9 - Multi-Site Management.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.site import (
    SiteCreate,
    SiteHealthResponse,
    SiteListResponse,
    SiteResponse,
    SiteSummaryResponse,
    SiteUpdate,
)
from app.services.site_service import SiteService, site_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sites",
    tags=["Sites"],
    dependencies=[Depends(get_current_user)],
)


def get_site_service() -> SiteService:
    return site_service


# ------------------------------------------------------------------ #
# List / Get                                                          #
# ------------------------------------------------------------------ #


@router.get("", response_model=SiteListResponse)
async def list_sites(
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteListResponse:
    """List all sites."""
    return await service.list_sites(db)


@router.get(
    "/summary",
    response_model=list[SiteSummaryResponse],
)
async def list_site_summaries(
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> list[SiteSummaryResponse]:
    """Compact site list for selector dropdown."""
    return await service.list_summaries(db)


@router.get(
    "/health",
    response_model=list[SiteHealthResponse],
)
async def list_sites_health(
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> list[SiteHealthResponse]:
    """Health status for all sites."""
    return await service.get_all_sites_health(db)


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
)
async def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Get a single site."""
    return await service.get_site(db, site_id)


@router.get(
    "/code/{code}",
    response_model=SiteResponse,
)
async def get_site_by_code(
    code: str,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Get a site by its code."""
    return await service.get_site_by_code(db, code)


# ------------------------------------------------------------------ #
# Create / Update / Delete                                            #
# ------------------------------------------------------------------ #


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SiteResponse,
)
async def create_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Create a new site."""
    return await service.create_site(db, payload)


@router.put(
    "/{site_id}",
    response_model=SiteResponse,
)
async def update_site(
    site_id: int,
    payload: SiteUpdate,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Update an existing site."""
    return await service.update_site(db, site_id, payload)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> None:
    """Delete a site."""
    await service.delete_site(db, site_id)


# ------------------------------------------------------------------ #
# Actions                                                             #
# ------------------------------------------------------------------ #


@router.post(
    "/{site_id}/enable",
    response_model=SiteResponse,
)
async def enable_site(
    site_id: int,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Enable a site."""
    return await service.enable_site(db, site_id)


@router.post(
    "/{site_id}/disable",
    response_model=SiteResponse,
)
async def disable_site(
    site_id: int,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Disable a site."""
    return await service.disable_site(db, site_id)


# ------------------------------------------------------------------ #
# Health                                                              #
# ------------------------------------------------------------------ #


@router.get(
    "/{site_id}/health",
    response_model=SiteHealthResponse,
)
async def get_site_health(
    site_id: int,
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteHealthResponse:
    """Get health status for a site."""
    return await service.get_site_health(db, site_id)
