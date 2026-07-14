"""
Mission Control Playbook Step Repository

All database access for PlaybookStep entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.playbook_step import PlaybookStep


class PlaybookStepRepository:
    """Data access layer for playbook step records."""

    @staticmethod
    def get_by_playbook(
        db: Session, playbook_id: int
    ) -> list[PlaybookStep]:
        stmt = (
            select(PlaybookStep)
            .where(PlaybookStep.playbook_id == playbook_id)
            .order_by(PlaybookStep.step_order)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, step_id: int
    ) -> PlaybookStep | None:
        stmt = select(PlaybookStep).where(PlaybookStep.id == step_id)
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        playbook_id: int,
        name: str,
        step_type: str,
        provider: str,
        command: str,
        step_order: int = 0,
        description: str | None = None,
        target_host: str | None = None,
        shell: str | None = None,
        working_directory: str | None = None,
        environment_variables: str | None = None,
        timeout_seconds: int = 300,
        retry_count: int = 0,
        continue_on_failure: bool = False,
        rollback_command: str | None = None,
    ) -> PlaybookStep:
        entity = PlaybookStep(
            playbook_id=playbook_id,
            name=name,
            step_type=step_type,
            provider=provider,
            command=command,
            step_order=step_order,
            description=description,
            target_host=target_host,
            shell=shell,
            working_directory=working_directory,
            environment_variables=environment_variables,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            continue_on_failure=continue_on_failure,
            rollback_command=rollback_command,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: PlaybookStep,
        **kwargs,
    ) -> PlaybookStep:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, entity: PlaybookStep) -> None:
        db.delete(entity)
        db.commit()
