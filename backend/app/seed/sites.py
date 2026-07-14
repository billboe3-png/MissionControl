"""Seed default sites."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.site import Site


def seed(db: Session) -> bool:
    """Insert default site when the table is empty."""
    count = db.scalar(select(func.count(Site.id)))
    if count > 0:
        return False

    now = datetime.now(UTC)
    db.add(
        Site(
            name="Default",
            code="default",
            description="Default site for Mission Control",
            color="#3b82f6",
            icon="🏠",
            enabled=True,
            is_default=True,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    return True
