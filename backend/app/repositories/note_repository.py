"""
Mission Control Note Repository

All database access for Note entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.db.note import Note
from app.schemas.note import NoteCreate
from app.schemas.note import NoteUpdate


class NoteRepository:
    """Data access layer for notes stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Note]:
        """
        Return all notes ordered by creation date descending.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of Note ORM instances.
        """
        stmt = (
            select(Note)
            .options(selectinload(Note.project))
            .order_by(Note.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, note_id: int) -> Note | None:
        """
        Return a single note by identifier.

        Args:
            db: Active SQLAlchemy session.
            note_id: Primary key of the note.

        Returns:
            Note ORM instance, or None if not found.
        """
        stmt = select(Note).where(Note.id == note_id)
        return db.scalar(stmt)

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
    def get_duplicate(
        db: Session,
        project_id: int,
        title: str,
    ) -> Note | None:
        """
        Return a note by project and title using a case-insensitive lookup.

        Args:
            db: Active SQLAlchemy session.
            project_id: Identifier of the parent project.
            title: Note title to search for.

        Returns:
            Note ORM instance, or None if not found.
        """
        normalized = title.strip().lower()
        stmt = select(Note).where(
            Note.project_id == project_id,
            func.lower(func.trim(Note.title)) == normalized,
        )
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, note: NoteCreate) -> Note:
        """
        Persist a new note.

        Args:
            db: Active SQLAlchemy session.
            note: Validated note creation payload.

        Returns:
            The persisted Note ORM instance.
        """
        entity = Note(
            project_id=note.project_id,
            title=note.title.strip(),
            content=note.content,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        note_id: int,
        note: NoteUpdate,
    ) -> Note | None:
        """
        Update an existing note with only the supplied fields.

        Args:
            db: Active SQLAlchemy session.
            note_id: Primary key of the note.
            note: Validated note update payload.

        Returns:
            Updated Note ORM instance, or None if not found.
        """
        entity = NoteRepository.get_by_id(db, note_id)
        if entity is None:
            return None

        updates = note.model_dump(exclude_unset=True)
        if "title" in updates and updates["title"] is not None:
            updates["title"] = updates["title"].strip()
        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, note_id: int) -> bool:
        """
        Delete a note by identifier.

        Args:
            db: Active SQLAlchemy session.
            note_id: Primary key of the note.

        Returns:
            True if deleted, False if the note was not found.
        """
        entity = NoteRepository.get_by_id(db, note_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True

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
