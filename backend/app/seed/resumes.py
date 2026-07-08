"""Seed default resume context."""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.resume import Resume


def seed(db: Session) -> bool:
    """Skip resume seeding when the production baseline leaves resumes empty."""
    count = db.scalar(select(func.count(Resume.id)))
    if count > 0:
        return False

    return False
