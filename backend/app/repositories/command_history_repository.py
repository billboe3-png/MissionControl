"""
Mission Control Command History Repository

All database access for CommandHistory entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.command_history import CommandHistory
from app.models.db.remote_host import RemoteHost


class CommandHistoryRepository:
    """Data access layer for command history records stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[CommandHistory]:
        """Return all history records ordered by start time descending."""
        stmt = select(CommandHistory).order_by(
            CommandHistory.started_at.desc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, history_id: int
    ) -> CommandHistory | None:
        """Return a single history record by identifier."""
        stmt = select(CommandHistory).where(
            CommandHistory.id == history_id
        )
        return db.scalar(stmt)

    @staticmethod
    def get_recent(db: Session, limit: int = 10) -> list[CommandHistory]:
        """Return the most recent history records up to the given limit."""
        stmt = (
            select(CommandHistory)
            .order_by(CommandHistory.started_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_filtered(
        db: Session,
        search: str | None = None,
        host_id: int | None = None,
        success: bool | None = None,
        limit: int = 50,
    ) -> list[CommandHistory]:
        """
        Return history records with optional filtering.

        Args:
            db: Active SQLAlchemy session.
            search: Filter by command text (case-insensitive LIKE).
            host_id: Filter by specific remote host.
            success: Filter by success status.
            limit: Maximum records to return (default 50).
        """
        stmt = select(CommandHistory)

        if search:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(CommandHistory.command).like(term))

        if host_id is not None:
            stmt = stmt.where(CommandHistory.host_id == host_id)

        if success is not None:
            stmt = stmt.where(CommandHistory.success.is_(success))

        stmt = (
            stmt.order_by(CommandHistory.started_at.desc()).limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(
        db: Session,
        host_id: int,
        command: str,
        shell: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        success: bool,
        duration_ms: int,
        executed_by: str | None = None,
        credential_id: int | None = None,
        username: str | None = None,
        working_directory: str | None = None,
        execution_source: str = "manual",
    ) -> CommandHistory:
        """Persist a new command history record."""
        entity = CommandHistory(
            host_id=host_id,
            command=command,
            shell=shell,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            success=success,
            duration_ms=duration_ms,
            executed_by=executed_by,
            credential_id=credential_id,
            username=username,
            working_directory=working_directory,
            execution_source=execution_source,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def attach_host_names(
        db: Session,
        records: list[CommandHistory],
    ) -> list[dict]:
        """
        Enrich history records with host names.

        Returns list of dicts ready for API response serialization.
        """
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
                "shell": r.shell,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "exit_code": r.exit_code,
                "success": r.success,
                "duration_ms": r.duration_ms,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "executed_by": r.executed_by,
                "username": r.username,
                "working_directory": r.working_directory,
                "execution_source": r.execution_source,
            }
            for r in records
        ]
