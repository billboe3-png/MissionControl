"""
Mission Control Site Router

API endpoints for managing sites.
Sprint 2.9 - Multi-Site Management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.core.rbac import company_scope_clause, entity_in_company_scope
from app.db import get_db
from app.models.db.site import Site
from app.models.db.user import User
from app.schemas.site import (
    SiteCreate,
    SiteHealthResponse,
    SiteListResponse,
    SiteResponse,
    SiteSummaryResponse,
    SiteUpdate,
)
from app.services.auth_service import require_role
from app.services.site_service import SiteService, site_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sites",
    tags=["Sites"],
    dependencies=[Depends(get_current_user)],
)


def get_site_service() -> SiteService:
    return site_service


def _get_scoped_site(db: Session, user: User, site_id: int) -> Site:
    """Fetch a site and verify it is visible to `user` (404 on mismatch)."""
    site = db.scalar(select(Site).where(Site.id == site_id))
    if site is None or not entity_in_company_scope(db, user, site.company_id):
        raise HTTPException(status_code=404, detail="Site not found")
    return site


def _scoped_site_ids(db: Session, user: User) -> list[int] | None:
    """Return site IDs visible to `user`; None means unrestricted (global)."""
    clause = company_scope_clause(db, user, Site)
    if clause is None:
        return None
    return list(db.scalars(select(Site.id).where(clause)).all())


# ------------------------------------------------------------------ #
# List / Get                                                          #
# ------------------------------------------------------------------ #


@router.get("", response_model=SiteListResponse)
async def list_sites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteListResponse:
    """List sites visible to the current user."""
    result = await service.list_sites(db)
    if current_user.role == "global_admin":
        return result
    result.items = [s for s in result.items if s.company_id == current_user.company_id]
    result.count = len(result.items)
    return result


@router.get(
    "/summary",
    response_model=list[SiteSummaryResponse],
)
async def list_site_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> list[SiteSummaryResponse]:
    """Compact site list for selector dropdown."""
    result = await service.list_summaries(db)
    scoped_ids = _scoped_site_ids(db, current_user)
    if scoped_ids is None:
        return result
    return [s for s in result if s.id in scoped_ids]


@router.get(
    "/health",
    response_model=list[SiteHealthResponse],
)
async def list_sites_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> list[SiteHealthResponse]:
    """Health status for sites visible to the current user."""
    result = await service.get_all_sites_health(db)
    scoped_ids = _scoped_site_ids(db, current_user)
    if scoped_ids is None:
        return result
    return [s for s in result if s.site_id in scoped_ids]


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
)
async def get_site(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Get a single site."""
    _get_scoped_site(db, current_user, site_id)
    return await service.get_site(db, site_id)


@router.get(
    "/code/{code}",
    response_model=SiteResponse,
)
async def get_site_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Get a site by its code."""
    site = await service.get_site_by_code(db, code)
    if site is None or not entity_in_company_scope(
        db, current_user, site.company_id
    ):
        raise HTTPException(status_code=404, detail="Site not found")
    return site


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Create a new site (company admins within their own company)."""
    require_role(current_user, "company_admin")
    if current_user.role != "global_admin":
        if (
            payload.company_id is not None
            and payload.company_id != current_user.company_id
        ):
            raise HTTPException(status_code=403, detail="Company not allowed")
        payload.company_id = current_user.company_id
    return await service.create_site(db, payload)


@router.put(
    "/{site_id}",
    response_model=SiteResponse,
)
async def update_site(
    site_id: int,
    payload: SiteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Update an existing site."""
    require_role(current_user, "company_admin")
    _get_scoped_site(db, current_user, site_id)
    return await service.update_site(db, site_id, payload)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_site(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> None:
    """Delete a site."""
    require_role(current_user, "company_admin")
    _get_scoped_site(db, current_user, site_id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Enable a site."""
    require_role(current_user, "company_admin")
    _get_scoped_site(db, current_user, site_id)
    return await service.enable_site(db, site_id)


@router.post(
    "/{site_id}/disable",
    response_model=SiteResponse,
)
async def disable_site(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteResponse:
    """Disable a site."""
    require_role(current_user, "company_admin")
    _get_scoped_site(db, current_user, site_id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: SiteService = Depends(get_site_service),
) -> SiteHealthResponse:
    """Get health status for a site."""
    _get_scoped_site(db, current_user, site_id)
    return await service.get_site_health(db, site_id)
