"""
Mission Control Event Trigger Repository

All database access for EventTrigger entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.event_trigger import EventTrigger


class EventTriggerRepository:
    """Data access layer for event trigger records."""

    @staticmethod
    def get_all(db: Session) -> list[EventTrigger]:
        stmt = select(EventTrigger).order_by(
            EventTrigger.created_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_playbook(
        db: Session, playbook_id: int
    ) -> list[EventTrigger]:
        stmt = (
            select(EventTrigger)
            .where(EventTrigger.playbook_id == playbook_id)
            .order_by(EventTrigger.created_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, trigger_id: int
    ) -> EventTrigger | None:
        stmt = select(EventTrigger).where(
            EventTrigger.id == trigger_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_enabled(db: Session) -> list[EventTrigger]:
        stmt = (
            select(EventTrigger)
            .where(EventTrigger.enabled.is_(True))
            .order_by(EventTrigger.event_type)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_event_type(
        db: Session, event_type: str
    ) -> list[EventTrigger]:
        stmt = (
            select(EventTrigger)
            .where(EventTrigger.event_type == event_type)
            .where(EventTrigger.enabled.is_(True))
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        playbook_id: int,
        name: str,
        event_type: str,
        conditions: str | None = None,
        enabled: bool = True,
    ) -> EventTrigger:
        entity = EventTrigger(
            playbook_id=playbook_id,
            name=name,
            event_type=event_type,
            conditions=conditions,
            enabled=enabled,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: EventTrigger,
        **kwargs,
    ) -> EventTrigger:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, entity: EventTrigger) -> None:
        db.delete(entity)
        db.commit()
