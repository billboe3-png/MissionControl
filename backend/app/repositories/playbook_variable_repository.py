"""
Mission Control Playbook Variable Repository

All database access for PlaybookVariable entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.playbook_variable import PlaybookVariable


class PlaybookVariableRepository:
    """Data access layer for playbook variable records."""

    @staticmethod
    def get_by_playbook(
        db: Session, playbook_id: int
    ) -> list[PlaybookVariable]:
        stmt = (
            select(PlaybookVariable)
            .where(PlaybookVariable.playbook_id == playbook_id)
            .order_by(PlaybookVariable.name)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, variable_id: int
    ) -> PlaybookVariable | None:
        stmt = select(PlaybookVariable).where(
            PlaybookVariable.id == variable_id
        )
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        playbook_id: int,
        name: str,
        value: str | None = None,
        variable_type: str = "string",
        description: str | None = None,
        required: bool = False,
        sensitive: bool = False,
        default_value: str | None = None,
    ) -> PlaybookVariable:
        entity = PlaybookVariable(
            playbook_id=playbook_id,
            name=name,
            value=value,
            variable_type=variable_type,
            description=description,
            required=required,
            sensitive=sensitive,
            default_value=default_value,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: PlaybookVariable,
        **kwargs,
    ) -> PlaybookVariable:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, entity: PlaybookVariable) -> None:
        db.delete(entity)
        db.commit()
