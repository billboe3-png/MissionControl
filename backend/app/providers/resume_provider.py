"""
Mission Control Resume Provider

Returns enriched resume data for the dashboard.
Includes current sprint context and activity status.
"""

import logging

from sqlalchemy.orm import Session

from app.models.db.resume import Resume

logger = logging.getLogger(__name__)


class ResumeProvider:
    """Return resume data for the dashboard."""

    def get_resume_data(self, db: Session) -> dict:
        """Return active resume or unavailable state."""
        active = (
            db.query(Resume)
            .where(Resume.available.is_(True))
            .order_by(Resume.updated_at.desc())
            .first()
        )

        if active is None:
            return {
                "available": False,
                "title": None,
                "description": None,
                "current_sprint": None,
                "current_goal": None,
                "current_project": None,
                "current_branch": None,
                "last_activity": None,
            }

        return {
            "available": active.available,
            "title": active.title,
            "description": active.description,
            "current_sprint": None,
            "current_goal": None,
            "current_project": None,
            "current_branch": None,
            "last_activity": active.updated_at.isoformat(),
        }


resume_provider = ResumeProvider()
