"""
Mission Control Note Service

Business logic for the Notes dashboard section.

Sprint:
    1.1.0C
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.db.note import Note
from app.repositories.note_repository import NoteRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate

logger = logging.getLogger(__name__)


class NoteService:
    """Notes dashboard section."""

    def __init__(self, repository: NoteRepository | None = None) -> None:
        self._repository = repository or NoteRepository()

    async def get_all(self, db: Session) -> NoteListResponse:
        """Return all notes as API response models."""
        logger.info("Fetching all notes")
        notes = self._repository.get_all(db)
        items = [NoteResponse.model_validate(note) for note in notes]
        return NoteListResponse(count=len(items), items=items)

    async def get_by_id(self, db: Session, note_id: int) -> NoteResponse:
        """Return a single note as an API response model."""
        logger.info("Fetching note id=%s", note_id)
        note = self._repository.get_by_id(db, note_id)
        if note is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )
        return NoteResponse.model_validate(note)

    async def create(self, db: Session, data: NoteCreate) -> NoteResponse:
        """Create a new note and return the API response model."""
        logger.info("Creating note: %s", data.title)

        if ProjectRepository().get_by_id(db, data.project_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if (
            self._repository.get_duplicate(
                db,
                data.project_id,
                data.title,
            )
            is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Note already exists",
            )

        note = self._repository.create(db, data)
        return NoteResponse.model_validate(note)

    async def update(
        self,
        db: Session,
        note_id: int,
        data: NoteUpdate,
    ) -> NoteResponse:
        """Update an existing note and return the API response model."""
        logger.info("Updating note id=%s", note_id)

        existing = self._repository.get_by_id(db, note_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        updates = data.model_dump(exclude_unset=True)

        if (
            "project_id" in updates
            and ProjectRepository().get_by_id(db, updates["project_id"]) is None
        ):
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

        new_project_id = updates.get("project_id", existing.project_id)
        new_title = updates.get("title", existing.title)
        combination_changes = False

        if (
            "project_id" in updates
            and updates["project_id"] != existing.project_id
        ):
            combination_changes = True
        if "title" in updates and updates["title"] is not None and (
            updates["title"].strip().lower()
            != existing.title.strip().lower()
        ):
            combination_changes = True

        if combination_changes:
            duplicate = self._repository.get_duplicate(
                db,
                new_project_id,
                new_title,
            )
            if duplicate is not None and duplicate.id != note_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Note already exists",
                )

        if "title" in updates and updates["title"] is not None:
            data = data.model_copy(update={"title": updates["title"].strip()})

        updated = self._repository.update(db, note_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )
        return NoteResponse.model_validate(updated)

    async def delete(self, db: Session, note_id: int) -> None:
        """Delete a note by identifier."""
        logger.info("Deleting note id=%s", note_id)

        deleted = self._repository.delete(db, note_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

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


note_service = NoteService()
