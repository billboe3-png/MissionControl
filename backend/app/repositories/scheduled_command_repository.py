"""
Mission Control Scheduled Command Repository

All database access for ScheduledCommand entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.scheduled_command import ScheduledCommand


class ScheduledCommandRepository:
    """Data access layer for scheduled commands."""

    @staticmethod
    def get_all(db: Session) -> list[ScheduledCommand]:
        stmt = select(ScheduledCommand).order_by(
            ScheduledCommand.id
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, schedule_id: int
    ) -> ScheduledCommand | None:
        stmt = select(ScheduledCommand).where(
            ScheduledCommand.id == schedule_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_enabled(db: Session) -> list[ScheduledCommand]:
        stmt = select(ScheduledCommand).where(
            ScheduledCommand.enabled.is_(True)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        host_id: int,
        credential_id: int | None,
        command: str,
        cron_expression: str,
        enabled: bool,
        next_run=None,
    ) -> ScheduledCommand:
        entity = ScheduledCommand(
            host_id=host_id,
            credential_id=credential_id,
            command=command,
            cron_expression=cron_expression,
            enabled=enabled,
            next_run=next_run,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        schedule_id: int,
        data: dict,
    ) -> ScheduledCommand | None:
        entity = ScheduledCommandRepository.get_by_id(db, schedule_id)
        if entity is None:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, schedule_id: int) -> bool:
        entity = ScheduledCommandRepository.get_by_id(db, schedule_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def attach_host_names(
        db: Session,
        records: list[ScheduledCommand],
    ) -> list[dict]:
        from app.models.db.remote_host import RemoteHost

        host_ids = {r.host_id for r in records}
        hosts: dict[int, str] = {}
        if host_ids:
            result = db.execute(
                select(RemoteHost.id, RemoteHost.name).where(
                    RemoteHost.id.in_(host_ids)
                )
            )
            hosts = {row[0]: row[1] for row in result.all()}

        return [
            {
                "id": r.id,
                "host_id": r.host_id,
                "host_name": hosts.get(r.host_id),
                "credential_id": r.credential_id,
                "command": r.command,
                "cron_expression": r.cron_expression,
                "enabled": r.enabled,
                "last_run": r.last_run,
                "next_run": r.next_run,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in records
        ]
