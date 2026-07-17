"""
Mission Control Site Service

Business logic for site management: CRUD, health, and statistics.
Sprint 2.9 - Multi-Site Management.
"""

import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.site import Site
from app.repositories.site_repository import SiteRepository
from app.schemas.site import (
    SiteCreate,
    SiteHealthResponse,
    SiteListResponse,
    SiteResponse,
    SiteSummaryResponse,
    SiteUpdate,
)

logger = logging.getLogger(__name__)


class SiteService:
    """Service layer for site management."""

    # ------------------------------------------------------------------ #
    # CRUD                                                                #
    # ------------------------------------------------------------------ #

    async def list_sites(self, db: Session) -> SiteListResponse:
        """List all sites with computed counts."""
        sites = SiteRepository.get_all(db)
        all_stats = SiteRepository.get_all_site_stats(db)
        all_company_names = self._get_company_names(db, sites)
        items = [
            self._to_response(s, db, all_stats=all_stats, all_company_names=all_company_names)
            for s in sites
        ]
        return SiteListResponse(count=len(items), items=items)

    async def list_summaries(
        self, db: Session
    ) -> list[SiteSummaryResponse]:
        """Compact list for site selector dropdown."""
        sites = SiteRepository.get_all(db)
        return [
            SiteSummaryResponse(
                id=s.id,
                name=s.name,
                code=s.code,
                color=s.color,
                icon=s.icon,
                enabled=s.enabled,
            )
            for s in sites
        ]

    async def get_site(
        self, db: Session, site_id: int
    ) -> SiteResponse:
        """Get a single site by ID."""
        site = SiteRepository.get_by_id(db, site_id)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )
        return self._to_response(site, db)

    async def get_site_by_code(
        self, db: Session, code: str
    ) -> SiteResponse:
        """Get a single site by code."""
        site = SiteRepository.get_by_code(db, code)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )
        return self._to_response(site, db)

    async def create_site(
        self, db: Session, data: SiteCreate
    ) -> SiteResponse:
        """Create a new site."""
        existing = SiteRepository.get_by_name(db, data.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A site with this name already exists",
            )

        existing_code = SiteRepository.get_by_code(db, data.code)
        if existing_code is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A site with this code already exists",
            )

        if data.is_default:
            self._clear_default_site(db)

        kwargs = {
            "name": data.name.strip(),
            "code": data.code.strip().lower(),
            "company_id": data.company_id,
            "description": data.description,
            "color": data.color,
            "icon": data.icon,
            "enabled": data.enabled,
            "is_default": data.is_default,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "country": data.country,
            "timezone": data.timezone,
            "contact_name": data.contact_name,
            "contact_email": data.contact_email,
            "contact_phone": data.contact_phone,
        }

        site = SiteRepository.create(db, **kwargs)
        return self._to_response(site, db)

    async def update_site(
        self, db: Session, site_id: int, data: SiteUpdate
    ) -> SiteResponse:
        """Update an existing site."""
        existing = SiteRepository.get_by_id(db, site_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )

        updates = data.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
            conflict = SiteRepository.get_by_name(
                db, updates["name"]
            )
            if conflict and conflict.id != site_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A site with this name already exists",
                )

        if "code" in updates and updates["code"] is not None:
            updates["code"] = updates["code"].strip().lower()
            conflict = SiteRepository.get_by_code(
                db, updates["code"]
            )
            if conflict and conflict.id != site_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A site with this code already exists",
                )

        if updates.get("is_default"):
            self._clear_default_site(db)

        site = SiteRepository.update(db, site_id, **updates)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )
        return self._to_response(site, db)

    async def delete_site(
        self, db: Session, site_id: int
    ) -> None:
        """Delete a site."""
        site = SiteRepository.get_by_id(db, site_id)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )

        stats = SiteRepository.get_site_stats(db, site_id)
        if (
            stats["integration_count"] > 0
            or stats["host_count"] > 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cannot delete site with associated "
                    "integrations or hosts. Reassign or remove "
                    "them first."
                ),
            )

        deleted = SiteRepository.delete(db, site_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )

    # ------------------------------------------------------------------ #
    # Actions                                                             #
    # ------------------------------------------------------------------ #

    async def enable_site(
        self, db: Session, site_id: int
    ) -> SiteResponse:
        """Enable a site."""
        site = SiteRepository.update(db, site_id, enabled=True)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )
        return self._to_response(site, db)

    async def disable_site(
        self, db: Session, site_id: int
    ) -> SiteResponse:
        """Disable a site."""
        site = SiteRepository.update(db, site_id, enabled=False)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )
        return self._to_response(site, db)

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def get_site_health(
        self, db: Session, site_id: int
    ) -> SiteHealthResponse:
        """Get aggregated health for a site."""
        site = SiteRepository.get_by_id(db, site_id)
        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )

        from app.models.db.integration_profile import (
            IntegrationProfile,
        )
        from app.models.db.remote_host import RemoteHost

        integration_count = db.scalar(
            select(func.count(IntegrationProfile.id)).where(
                IntegrationProfile.site_id == site_id
            )
        ) or 0

        enabled_integrations = db.scalar(
            select(func.count(IntegrationProfile.id)).where(
                IntegrationProfile.site_id == site_id,
                IntegrationProfile.enabled.is_(True),
            )
        ) or 0

        host_count = db.scalar(
            select(func.count(RemoteHost.id)).where(
                RemoteHost.site_id == site_id
            )
        ) or 0

        enabled_hosts = db.scalar(
            select(func.count(RemoteHost.id)).where(
                RemoteHost.site_id == site_id,
                RemoteHost.enabled.is_(True),
            )
        ) or 0

        issues = []
        if integration_count > 0 and enabled_integrations == 0:
            issues.append("No integrations enabled")
        if host_count > 0 and enabled_hosts == 0:
            issues.append("No hosts enabled")
        if not site.enabled:
            issues.append("Site is disabled")

        if not site.enabled:
            health = "critical"
        elif issues:
            health = "warning"
        elif integration_count == 0 and host_count == 0:
            health = "unknown"
        else:
            health = "healthy"

        return SiteHealthResponse(
            site_id=site.id,
            site_name=site.name,
            site_code=site.code,
            health=health,
            integration_count=integration_count,
            enabled_integrations=enabled_integrations,
            host_count=host_count,
            enabled_hosts=enabled_hosts,
            issues=issues,
        )

    async def get_all_sites_health(
        self, db: Session
    ) -> list[SiteHealthResponse]:
        """Get health for all sites."""
        sites = SiteRepository.get_all(db)
        results = []
        for site in sites:
            health = await self.get_site_health(db, site.id)
            results.append(health)
        return results

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_company_names(db: Session, sites: list[Site]) -> dict[int, str]:
        """Batch-load company display names for a list of sites."""
        company_ids = {s.company_id for s in sites if s.company_id is not None}
        if not company_ids:
            return {}
        from app.models.db.company import Company

        rows = db.execute(
            select(Company.id, Company.display_name).where(
                Company.id.in_(company_ids)
            )
        ).all()
        return {row.id: row.display_name for row in rows}

    def _to_response(
        self,
        site: Site,
        db: Session,
        all_stats: dict | None = None,
        all_company_names: dict | None = None,
    ) -> SiteResponse:
        """Convert an ORM site to a response with computed counts."""
        if all_stats is not None:
            stats = all_stats.get(
                site.id, {"integration_count": 0, "host_count": 0}
            )
        else:
            stats = SiteRepository.get_site_stats(db, site.id)

        company_name = None
        if all_company_names is not None:
            company_name = all_company_names.get(site.company_id) if site.company_id else None
        elif site.company_id is not None:
            try:
                from sqlalchemy import select as sel

                from app.models.db.company import Company

                company = db.scalar(
                    sel(Company).where(Company.id == site.company_id)
                )
                if company is not None:
                    company_name = company.display_name
            except Exception:
                pass

        return SiteResponse(
            id=site.id,
            name=site.name,
            code=site.code,
            company_id=site.company_id,
            company_name=company_name,
            description=site.description,
            color=site.color,
            icon=site.icon,
            enabled=site.enabled,
            is_default=site.is_default,
            address=site.address,
            city=site.city,
            state=site.state,
            country=site.country,
            timezone=site.timezone,
            contact_name=site.contact_name,
            contact_email=site.contact_email,
            contact_phone=site.contact_phone,
            integration_count=stats["integration_count"],
            host_count=stats["host_count"],
            created_at=site.created_at,
            updated_at=site.updated_at,
        )

    def _clear_default_site(self, db: Session) -> None:
        """Clear is_default from all other sites."""
        default = SiteRepository.get_default(db)
        if default is not None:
            default.is_default = False
            default.updated_at = datetime.now(UTC)
            db.flush()


site_service = SiteService()
