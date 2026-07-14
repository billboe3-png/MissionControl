"""
Mission Control Playbook Execution Repository

All database access for PlaybookExecution entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.playbook_execution import PlaybookExecution


class PlaybookExecutionRepository:
    """Data access layer for playbook execution records."""

    @staticmethod
    def get_all(db: Session) -> list[PlaybookExecution]:
        stmt = select(PlaybookExecution).order_by(
            PlaybookExecution.created_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, execution_id: int
    ) -> PlaybookExecution | None:
        stmt = select(PlaybookExecution).where(
            PlaybookExecution.id == execution_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_by_playbook(
        db: Session, playbook_id: int, limit: int = 50
    ) -> list[PlaybookExecution]:
        stmt = (
            select(PlaybookExecution)
            .where(PlaybookExecution.playbook_id == playbook_id)
            .order_by(PlaybookExecution.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_filtered(
        db: Session,
        playbook_id: int | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[PlaybookExecution]:
        stmt = select(PlaybookExecution)

        if playbook_id is not None:
            stmt = stmt.where(
                PlaybookExecution.playbook_id == playbook_id
            )

        if status:
            stmt = stmt.where(PlaybookExecution.status == status)

        stmt = stmt.order_by(PlaybookExecution.created_at.desc()).limit(
            limit
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        playbook_id: int,
        status: str = "pending",
        mode: str = "live",
        trigger_type: str = "manual",
        triggered_by: str | None = None,
        variables_used: str | None = None,
        steps_total: int = 0,
        approval_required: bool = False,
    ) -> PlaybookExecution:
        entity = PlaybookExecution(
            playbook_id=playbook_id,
            status=status,
            mode=mode,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            variables_used=variables_used,
            steps_total=steps_total,
            approval_required=approval_required,
            approval_status="pending" if approval_required else None,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: PlaybookExecution,
        **kwargs,
    ) -> PlaybookExecution:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def count(db: Session) -> int:
        return db.scalar(
            select(func.count()).select_from(PlaybookExecution)
        ) or 0

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        return db.scalar(
            select(func.count())
            .select_from(PlaybookExecution)
            .where(PlaybookExecution.status == status)
        ) or 0
