"""
Mission Control Note Repository

All database access for Note entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.note import Note


class NoteRepository:
    """Data access layer for notes stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Note]:
        """
        Return all notes ordered by id.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Note ORM instances.
        """
        stmt = select(Note).order_by(Note.id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_count(db: Session) -> int:
        """
        Return the total number of notes.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Note count from PostgreSQL.
        """
        stmt = select(func.count()).select_from(Note)
        return db.scalar(stmt) or 0

    @staticmethod
    def create_many(db: Session, notes: list[Note]) -> list[Note]:
        """
        Persist multiple notes in a single transaction.

        Args:
            db: Active SQLAlchemy session.
            notes: Note ORM instances to insert.

        Returns:
            The persisted Note ORM instances.
        """
        db.add_all(notes)
        db.commit()
        for note in notes:
            db.refresh(note)
        return notes
