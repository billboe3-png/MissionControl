"""Seed default notes."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.note import Note


def seed(db: Session) -> bool:
    """Skip note seeding when the production baseline leaves notes empty."""
    count = db.scalar(select(func.count(Note.id)))
    if count > 0:
        return False

    return False
