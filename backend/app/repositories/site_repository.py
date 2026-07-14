"""
Mission Control Site Repository

Data access layer for Site entities.
Sprint 2.9 - Multi-Site Management.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.site import Site


class SiteRepository:
    """Data access layer for sites stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Site]:
        """Return all sites ordered by name."""
        stmt = select(Site).order_by(Site.name.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, site_id: int) -> Site | None:
        """Return a single site by identifier."""
        stmt = select(Site).where(Site.id == site_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_code(db: Session, code: str) -> Site | None:
        """Return a single site by code."""
        stmt = select(Site).where(Site.code == code)
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Site | None:
        """Return a single site by name."""
        stmt = select(Site).where(Site.name == name)
        return db.scalar(stmt)

    @staticmethod
    def get_default(db: Session) -> Site | None:
        """Return the default site."""
        stmt = select(Site).where(Site.is_default.is_(True))
        return db.scalar(stmt)

    @staticmethod
    def get_enabled(db: Session) -> list[Site]:
        """Return all enabled sites ordered by name."""
        stmt = (
            select(Site)
            .where(Site.enabled.is_(True))
            .order_by(Site.name.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def count(db: Session) -> int:
        """Return total number of sites."""
        return db.scalar(select(func.count(Site.id))) or 0

    @staticmethod
    def count_enabled(db: Session) -> int:
        """Return number of enabled sites."""
        stmt = (
            select(func.count())
            .select_from(Site)
            .where(Site.enabled.is_(True))
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def create(db: Session, **kwargs) -> Site:
        """Persist a new site."""
        entity = Site(**kwargs)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, site_id: int, **kwargs) -> Site | None:
        """Update an existing site."""
        entity = SiteRepository.get_by_id(db, site_id)
        if entity is None:
            return None

        for field, value in kwargs.items():
            if value is not None:
                setattr(entity, field, value)

        entity.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, site_id: int) -> bool:
        """Delete a site by identifier."""
        entity = SiteRepository.get_by_id(db, site_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def get_site_stats(db: Session, site_id: int) -> dict:
        """Return integration and host counts for a site."""
        from app.models.db.integration_profile import IntegrationProfile
        from app.models.db.remote_host import RemoteHost

        integration_count = db.scalar(
            select(func.count(IntegrationProfile.id)).where(
                IntegrationProfile.site_id == site_id
            )
        ) or 0

        host_count = db.scalar(
            select(func.count(RemoteHost.id)).where(
                RemoteHost.site_id == site_id
            )
        ) or 0

        return {
            "integration_count": integration_count,
            "host_count": host_count,
        }
