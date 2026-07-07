"""
Mission Control Database Base

Defines the SQLAlchemy Declarative Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass
