"""
Mission Control Company Repository

Data access layer for Company entities.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.company import Company


class CompanyRepository:
    """Data access layer for companies stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Company]:
        """Return all companies ordered by name."""
        stmt = select(Company).order_by(Company.name.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, company_id: int) -> Company | None:
        """Return a single company by identifier."""
        stmt = select(Company).where(Company.id == company_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_uuid(db: Session, uuid: str) -> Company | None:
        """Return a single company by UUID."""
        stmt = select(Company).where(Company.uuid == uuid)
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Company | None:
        """Return a single company by name."""
        stmt = select(Company).where(Company.name == name)
        return db.scalar(stmt)

    @staticmethod
    def get_enabled(db: Session) -> list[Company]:
        """Return all enabled companies ordered by name."""
        stmt = (
            select(Company)
            .where(Company.enabled.is_(True))
            .order_by(Company.name.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def count(db: Session) -> int:
        """Return total number of companies."""
        return db.scalar(select(func.count(Company.id))) or 0

    @staticmethod
    def count_enabled(db: Session) -> int:
        """Return number of enabled companies."""
        stmt = (
            select(func.count())
            .select_from(Company)
            .where(Company.enabled.is_(True))
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def create(db: Session, **kwargs) -> Company:
        """Persist a new company."""
        entity = Company(**kwargs)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, company_id: int, **kwargs) -> Company | None:
        """Update an existing company."""
        entity = CompanyRepository.get_by_id(db, company_id)
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
    def delete(db: Session, company_id: int) -> bool:
        """Delete a company by identifier."""
        entity = CompanyRepository.get_by_id(db, company_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def get_company_stats(db: Session, company_id: int) -> dict:
        """Return site, agent, and integration counts for a company."""
        from app.models.db.agent import Agent
        from app.models.db.integration_profile import IntegrationProfile
        from app.models.db.site import Site

        site_count = db.scalar(
            select(func.count(Site.id)).where(
                Site.company_id == company_id
            )
        ) or 0

        agent_count = db.scalar(
            select(func.count(Agent.id)).where(
                Agent.company_id == company_id
            )
        ) or 0

        integration_count = db.scalar(
            select(func.count(IntegrationProfile.id)).where(
                IntegrationProfile.company_id == company_id
            )
        ) or 0

        return {
            "site_count": site_count,
            "agent_count": agent_count,
            "integration_count": integration_count,
        }

    @staticmethod
    def get_all_company_stats(db: Session) -> dict[int, dict]:
        """Return site/agent/integration counts for ALL companies in one query.

        Returns a dict keyed by company_id.
        """
        from app.models.db.agent import Agent
        from app.models.db.integration_profile import IntegrationProfile
        from app.models.db.site import Site

        site_counts = dict(
            db.execute(
                select(
                    Site.company_id,
                    func.count(Site.id).label("cnt"),
                )
                .where(Site.company_id.isnot(None))
                .group_by(Site.company_id)
            ).all()
        )
        agent_counts = dict(
            db.execute(
                select(
                    Agent.company_id,
                    func.count(Agent.id).label("cnt"),
                )
                .where(Agent.company_id.isnot(None))
                .group_by(Agent.company_id)
            ).all()
        )
        integration_counts = dict(
            db.execute(
                select(
                    IntegrationProfile.company_id,
                    func.count(IntegrationProfile.id).label("cnt"),
                )
                .where(IntegrationProfile.company_id.isnot(None))
                .group_by(IntegrationProfile.company_id)
            ).all()
        )

        all_ids = set(site_counts) | set(agent_counts) | set(integration_counts)
        return {
            cid: {
                "site_count": site_counts.get(cid, 0),
                "agent_count": agent_counts.get(cid, 0),
                "integration_count": integration_counts.get(cid, 0),
            }
            for cid in all_ids
        }
