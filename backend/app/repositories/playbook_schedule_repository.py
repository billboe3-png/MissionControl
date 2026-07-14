"""
Mission Control Playbook Schedule Repository

All database access for PlaybookSchedule entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.playbook_schedule import PlaybookSchedule


class PlaybookScheduleRepository:
    """Data access layer for playbook schedule records."""

    @staticmethod
    def get_all(db: Session) -> list[PlaybookSchedule]:
        stmt = select(PlaybookSchedule).order_by(
            PlaybookSchedule.created_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_playbook(
        db: Session, playbook_id: int
    ) -> list[PlaybookSchedule]:
        stmt = (
            select(PlaybookSchedule)
            .where(PlaybookSchedule.playbook_id == playbook_id)
            .order_by(PlaybookSchedule.created_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, schedule_id: int
    ) -> PlaybookSchedule | None:
        stmt = select(PlaybookSchedule).where(
            PlaybookSchedule.id == schedule_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_enabled(db: Session) -> list[PlaybookSchedule]:
        stmt = (
            select(PlaybookSchedule)
            .where(PlaybookSchedule.enabled.is_(True))
            .order_by(PlaybookSchedule.next_run)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        playbook_id: int,
        name: str,
        cron_expression: str,
        enabled: bool = True,
        variables_override: str | None = None,
    ) -> PlaybookSchedule:
        entity = PlaybookSchedule(
            playbook_id=playbook_id,
            name=name,
            cron_expression=cron_expression,
            enabled=enabled,
            variables_override=variables_override,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: PlaybookSchedule,
        **kwargs,
    ) -> PlaybookSchedule:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, entity: PlaybookSchedule) -> None:
        db.delete(entity)
        db.commit()
