"""
Mission Control Integration Profile Repository

Data access layer for IntegrationProfile entities.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.integration_profile import IntegrationProfile


class IntegrationProfileRepository:
    """Data access layer for integration profiles stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[IntegrationProfile]:
        """Return all integration profiles ordered by creation date."""
        stmt = select(IntegrationProfile).order_by(
            IntegrationProfile.created_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, profile_id: int
    ) -> IntegrationProfile | None:
        """Return a single integration profile by identifier."""
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.id == profile_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_by_type(
        db: Session, integration_type: str
    ) -> list[IntegrationProfile]:
        """Return all integration profiles of a given type."""
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.integration_type == integration_type
        ).order_by(IntegrationProfile.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_enabled_by_type(
        db: Session, integration_type: str
    ) -> IntegrationProfile | None:
        """Return the first enabled integration profile of a given type."""
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.integration_type == integration_type,
            IntegrationProfile.enabled.is_(True),
        ).order_by(IntegrationProfile.created_at.desc())
        return db.scalar(stmt)

    @staticmethod
    def get_all_enabled_by_type(
        db: Session, integration_type: str
    ) -> list[IntegrationProfile]:
        """Return all enabled integration profiles of a given type."""
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.integration_type == integration_type,
            IntegrationProfile.enabled.is_(True),
        ).order_by(IntegrationProfile.name.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_type(db: Session) -> dict[str, int]:
        """Return counts of profiles grouped by integration type."""
        stmt = (
            select(
                IntegrationProfile.integration_type,
                func.count(),
            )
            .group_by(IntegrationProfile.integration_type)
        )
        return {row[0]: row[1] for row in db.execute(stmt).all()}

    @staticmethod
    def count_enabled(db: Session) -> int:
        """Return the number of enabled integration profiles."""
        stmt = (
            select(func.count())
            .select_from(IntegrationProfile)
            .where(IntegrationProfile.enabled.is_(True))
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def get_by_site(db: Session, site_id: int) -> list[IntegrationProfile]:
        """Return all integration profiles for a given site."""
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.site_id == site_id
        ).order_by(IntegrationProfile.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_site(db: Session, site_id: int) -> int:
        """Return the number of integration profiles for a given site."""
        stmt = (
            select(func.count())
            .select_from(IntegrationProfile)
            .where(IntegrationProfile.site_id == site_id)
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def create(
        db: Session,
        name: str,
        integration_type: str,
        **kwargs,
    ) -> IntegrationProfile:
        """Persist a new integration profile."""
        entity = IntegrationProfile(
            name=name.strip(),
            integration_type=integration_type,
            **kwargs,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        profile_id: int,
        **kwargs,
    ) -> IntegrationProfile | None:
        """Update an existing integration profile."""
        entity = IntegrationProfileRepository.get_by_id(db, profile_id)
        if entity is None:
            return None

        for field, value in kwargs.items():
            if value is not None:
                setattr(entity, field, value)
            elif hasattr(entity, field):
                setattr(entity, field, None)

        entity.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, profile_id: int) -> bool:
        """Delete an integration profile by identifier."""
        entity = IntegrationProfileRepository.get_by_id(db, profile_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True
