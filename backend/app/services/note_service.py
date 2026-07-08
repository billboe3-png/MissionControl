"""
Mission Control Note Service

Business logic for the Notes dashboard section.

Sprint:
    1.1.0C
"""

from sqlalchemy.orm import Session

from app.models.db.note import Note
from app.repositories.note_repository import NoteRepository


class NoteService:
    """Notes dashboard section."""

    def __init__(self, repository: NoteRepository | None = None) -> None:
        self._repository = repository or NoteRepository()

    async def get_data(self, db: Session) -> dict:
        """
        Return note count and items loaded from PostgreSQL.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Dashboard notes payload with count and serialized items.
        """
        count = self._repository.get_count(db)
        notes = self._repository.get_all(db)

        return {
            "count": count,
            "items": [self._serialize_note(note) for note in notes],
        }

    @staticmethod
    def _serialize_note(note: Note) -> dict:
        """
        Map a Note ORM instance to the dashboard item shape.
        """
        return {
            "id": str(note.id),
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }


note_service = NoteService()
