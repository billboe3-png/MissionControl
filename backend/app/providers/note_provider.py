"""
Mission Control Note Provider

Returns aggregated note data for the dashboard.
Supports search by title and content.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.db.note import Note

logger = logging.getLogger(__name__)


class NoteProvider:
    """Return note statistics and data for the dashboard."""

    def get_note_data(self, db: Session) -> dict:
        """Return note count and recent items with project info."""
        total = db.scalar(
            select(func.count()).select_from(Note)
        ) or 0

        recent = (
            db.query(Note)
            .options(selectinload(Note.project))
            .order_by(Note.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "count": total,
            "items": [self._serialize(n) for n in recent],
        }

    @staticmethod
    def _serialize(note: Note) -> dict:
        project_name = note.project.name if note.project else None
        return {
            "id": str(note.id),
            "project_id": str(note.project_id) if note.project_id else None,
            "project_name": project_name,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }


note_provider = NoteProvider()
