"""Seed default projects."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.project import Project


def seed(db: Session) -> bool:
    """Insert default projects when the table is empty."""
    count = db.scalar(select(func.count(Project.id)))
    if count > 0:
        return False

    now = datetime.now(UTC)
    db.add_all(
        [
            Project(
                name="Mission Control",
                description=(
                    "Personal productivity platform and developer CLI "
                    "for managing IT operations from a single dashboard."
                ),
                active=True,
                created_at=now,
                updated_at=now,
            ),
            Project(
                name="UnitSphere",
                description=(
                    "Unified infrastructure and automation platform "
                    "for coordinating services across the environment."
                ),
                active=True,
                created_at=now,
                updated_at=now,
            ),
            Project(
                name="Infrastructure Upgrade",
                description=(
                    "Modernize core network, server, and monitoring "
                    "infrastructure to improve reliability and performance."
                ),
                active=True,
                created_at=now,
                updated_at=now,
            ),
            Project(
                name="Automation Scripts",
                description=(
                    "Collection of PowerShell and Python automation scripts "
                    "for routine operational tasks and deployments."
                ),
                active=True,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()
    return True
