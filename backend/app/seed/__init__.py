"""Production database seed package."""

from app.seed.notes import seed as seed_notes
from app.seed.parking_lot import seed as seed_parking_lot
from app.seed.projects import seed as seed_projects
from app.seed.resumes import seed as seed_resumes
from app.seed.tasks import seed as seed_tasks

__all__ = [
    "seed_notes",
    "seed_parking_lot",
    "seed_projects",
    "seed_resumes",
    "seed_tasks",
]
