"""
Mission Control Execution Log Repository

All database access for ExecutionLog entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.execution_log import ExecutionLog


class ExecutionLogRepository:
    """Data access layer for execution log records."""

    @staticmethod
    def get_by_execution(
        db: Session, execution_id: int
    ) -> list[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.execution_id == execution_id)
            .order_by(ExecutionLog.timestamp)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_step(
        db: Session, step_id: int
    ) -> list[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.step_id == step_id)
            .order_by(ExecutionLog.timestamp)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        execution_id: int,
        level: str,
        message: str,
        step_id: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        exit_code: int | None = None,
        duration_ms: int | None = None,
    ) -> ExecutionLog:
        entity = ExecutionLog(
            execution_id=execution_id,
            step_id=step_id,
            level=level,
            message=message,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity
