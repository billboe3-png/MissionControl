"""Repository for MikroTik plugin persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.plugins.installed.official_mikrotik.models import (
    MikroTikCommandLog,
    MikroTikServer,
)


class MikroTikRepository:
    """CRUD helpers for servers and the command audit log."""

    # ------------------------------------------------------------------ #
    # Servers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_servers(db: Session, enabled_only: bool = False) -> list[MikroTikServer]:
        stmt = select(MikroTikServer).order_by(MikroTikServer.id)
        if enabled_only:
            stmt = stmt.where(MikroTikServer.enabled.is_(True))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_server(db: Session, server_id: int) -> MikroTikServer | None:
        return db.get(MikroTikServer, server_id)

    @staticmethod
    def get_server_by_name(db: Session, name: str) -> MikroTikServer | None:
        return db.execute(
            select(MikroTikServer).where(MikroTikServer.name == name)
        ).scalar_one_or_none()

    @staticmethod
    def create_server(db: Session, **fields: object) -> MikroTikServer:
        server = MikroTikServer(**fields)
        db.add(server)
        db.flush()
        return server

    @staticmethod
    def update_server(db: Session, server: MikroTikServer, **fields: object) -> MikroTikServer:
        for key, value in fields.items():
            setattr(server, key, value)
        db.flush()
        return server

    @staticmethod
    def delete_server(db: Session, server: MikroTikServer) -> None:
        db.delete(server)
        db.flush()

    # ------------------------------------------------------------------ #
    # Command audit log                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_command_log(db: Session, **fields: object) -> MikroTikCommandLog:
        entry = MikroTikCommandLog(**fields)
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def list_command_logs(
        db: Session, server_id: int, limit: int = 50
    ) -> list[MikroTikCommandLog]:
        stmt = (
            select(MikroTikCommandLog)
            .where(MikroTikCommandLog.server_id == server_id)
            .order_by(MikroTikCommandLog.created_at.desc(), MikroTikCommandLog.id.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())
