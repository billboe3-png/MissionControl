"""
Mission Control Command Template Repository

All database access for CommandTemplate entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.command_template import CommandTemplate


class CommandTemplateRepository:
    """Data access layer for command templates."""

    @staticmethod
    def get_all(db: Session) -> list[CommandTemplate]:
        stmt = select(CommandTemplate).order_by(
            CommandTemplate.name
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, template_id: int
    ) -> CommandTemplate | None:
        stmt = select(CommandTemplate).where(
            CommandTemplate.id == template_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(
        db: Session, name: str
    ) -> CommandTemplate | None:
        stmt = select(CommandTemplate).where(
            CommandTemplate.name == name
        )
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        name: str,
        description: str | None,
        protocol: str,
        command: str,
        category: str | None,
    ) -> CommandTemplate:
        entity = CommandTemplate(
            name=name,
            description=description,
            protocol=protocol,
            command=command,
            category=category,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        template_id: int,
        data: dict,
    ) -> CommandTemplate | None:
        entity = CommandTemplateRepository.get_by_id(db, template_id)
        if entity is None:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, template_id: int) -> bool:
        entity = CommandTemplateRepository.get_by_id(db, template_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True
