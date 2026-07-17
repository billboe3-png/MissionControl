"""
Mission Control Playbook Repository

All database access for Playbook entities.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.playbook import Playbook


class PlaybookRepository:
    """Data access layer for playbook records."""

    @staticmethod
    def get_all(
        db: Session,
        company_id: int | None = None,
        site_id: int | None = None,
    ) -> list[Playbook]:
        stmt = select(Playbook)
        if company_id is not None:
            stmt = stmt.where(Playbook.company_id == company_id)
        if site_id is not None:
            stmt = stmt.where(Playbook.site_id == site_id)
        stmt = stmt.order_by(Playbook.updated_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, playbook_id: int) -> Playbook | None:
        stmt = select(Playbook).where(Playbook.id == playbook_id)
        return db.scalar(stmt)

    @staticmethod
    def get_filtered(
        db: Session,
        search: str | None = None,
        category: str | None = None,
        enabled: bool | None = None,
        company_id: int | None = None,
        site_id: int | None = None,
    ) -> list[Playbook]:
        stmt = select(Playbook)

        if company_id is not None:
            stmt = stmt.where(Playbook.company_id == company_id)
        if site_id is not None:
            stmt = stmt.where(Playbook.site_id == site_id)

        if search:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(Playbook.name).like(term))

        if category:
            stmt = stmt.where(Playbook.category == category)

        if enabled is not None:
            stmt = stmt.where(Playbook.enabled.is_(enabled))

        stmt = stmt.order_by(Playbook.updated_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        name: str,
        description: str | None = None,
        category: str | None = None,
        tags: str | None = None,
        enabled: bool = True,
        requires_approval: bool = False,
        auto_rollback: bool = False,
        timeout_seconds: int = 3600,
        max_retries: int = 0,
        created_by: str | None = None,
    ) -> Playbook:
        entity = Playbook(
            name=name,
            description=description,
            category=category,
            tags=tags,
            enabled=enabled,
            requires_approval=requires_approval,
            auto_rollback=auto_rollback,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            created_by=created_by,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: Playbook,
        **kwargs,
    ) -> Playbook:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, entity: Playbook) -> None:
        db.delete(entity)
        db.commit()

    @staticmethod
    def count(db: Session) -> int:
        return db.scalar(select(func.count()).select_from(Playbook)) or 0
