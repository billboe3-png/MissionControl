"""
Mission Control Notes Router

Sprint:
    1.3.2 - Note API Foundation
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.note import NoteCreate
from app.schemas.note import NoteListResponse
from app.schemas.note import NoteResponse
from app.schemas.note import NoteUpdate
from app.services.note_service import NoteService
from app.services.note_service import note_service

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


def get_note_service() -> NoteService:
    """Provide the shared note service instance."""
    return note_service


@router.get(
    "",
    summary="List notes",
    description="Return all notes managed by Mission Control.",
    response_model=NoteListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Notes retrieved successfully.",
            "model": NoteListResponse,
        },
    },
)
async def list_notes(
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
) -> NoteListResponse:
    return await service.get_all(db)


@router.get(
    "/{note_id}",
    summary="Get note",
    description="Return a single note by its identifier.",
    response_model=NoteResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Note retrieved successfully.",
            "model": NoteResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Note not found.",
        },
    },
)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    return await service.get_by_id(db, note_id)


@router.post(
    "",
    summary="Create note",
    description="Create a new note record.",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Note created successfully.",
            "model": NoteResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Note title already exists in project.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    return await service.create(db, payload)


@router.put(
    "/{note_id}",
    summary="Update note",
    description="Replace note fields for an existing note.",
    response_model=NoteResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Note updated successfully.",
            "model": NoteResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Note or project not found.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Note title already exists in project.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    return await service.update(db, note_id, payload)


@router.delete(
    "/{note_id}",
    summary="Delete note",
    description="Remove a note by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Note deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Note not found.",
        },
    },
)
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    service: NoteService = Depends(get_note_service),
) -> None:
    await service.delete(db, note_id)
