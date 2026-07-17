"""Production database seed runner."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.seed.automation import seed as seed_automation
from app.seed.notes import seed as seed_notes
from app.seed.parking_lot import seed as seed_parking_lot
from app.seed.projects import seed as seed_projects
from app.seed.resumes import seed as seed_resumes
from app.seed.sites import seed as seed_sites
from app.seed.tasks import seed as seed_tasks

logger = logging.getLogger(__name__)

SeedFunction = Callable[[Session], bool]

SEED_MODULES: list[tuple[str, SeedFunction]] = [
    ("Sites", seed_sites),
    ("Projects", seed_projects),
    ("Tasks", seed_tasks),
    ("Notes", seed_notes),
    ("Resume", seed_resumes),
    ("Parking Lot", seed_parking_lot),
    ("Automation Playbooks", seed_automation),
]


def run_seed() -> int:
    """Execute all seed modules and return a process exit code."""
    logger.info("Running database seed...")

    db = SessionLocal()
    try:
        for label, seed_func in SEED_MODULES:
            try:
                inserted = seed_func(db)
            except Exception:
                logger.exception("Failed to seed %s.", label)
                db.rollback()
                return 1

            if inserted:
                logger.info("%s seeded.", label)
            else:
                logger.info("%s already exist.", label)

        logger.info("Database seed completed.")
        return 0
    finally:
        db.close()


def main() -> None:
    """Configure logging and run the seed process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    sys.exit(run_seed())


if __name__ == "__main__":
    main()
