"""Seed default parking lot items."""

from sqlalchemy.orm import Session


def seed(db: Session) -> bool:
    """
    Parking lot persistence is not yet implemented.

    This module exists so future parking lot seeding can be added without
    changing the runner contract.
    """
    return False
