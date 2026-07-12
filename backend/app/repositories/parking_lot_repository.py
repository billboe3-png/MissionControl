"""
Mission Control Parking Lot Repository

All database access for Parking Lot entities.
"""

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.parking_lot import ParkingLot
from app.schemas.parking_lot import ParkingLotCreate
from app.schemas.parking_lot import ParkingLotUpdate


class ParkingLotRepository:
    """Data access layer for parking lot items stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[ParkingLot]:
        """
        Return all parking lot items ordered by updated_at descending.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of ParkingLot ORM instances.
        """
        stmt = select(ParkingLot).order_by(ParkingLot.updated_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, parking_lot_id: int) -> ParkingLot | None:
        """
        Return a single parking lot item by identifier.

        Args:
            db: Active SQLAlchemy session.
            parking_lot_id: Primary key of the parking lot item.

        Returns:
            ParkingLot ORM instance, or None if not found.
        """
        stmt = select(ParkingLot).where(ParkingLot.id == parking_lot_id)
        return db.scalar(stmt)

    @staticmethod
    def get_count(db: Session) -> int:
        """
        Return the total number of parking lot items.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Parking lot item count from PostgreSQL.
        """
        stmt = select(func.count()).select_from(ParkingLot)
        return db.scalar(stmt) or 0

    @staticmethod
    def create(db: Session, data: ParkingLotCreate) -> ParkingLot:
        """
        Persist a new parking lot item.

        Args:
            db: Active SQLAlchemy session.
            data: Validated parking lot creation payload.

        Returns:
            The persisted ParkingLot ORM instance.
        """
        entity = ParkingLot(
            title=data.title.strip(),
            description=data.description,
            priority=data.priority,
            status=data.status,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        parking_lot_id: int,
        data: ParkingLotUpdate,
    ) -> ParkingLot | None:
        """
        Update an existing parking lot item with only the supplied fields.

        Args:
            db: Active SQLAlchemy session.
            parking_lot_id: Primary key of the parking lot item.
            data: Validated parking lot update payload.

        Returns:
            Updated ParkingLot ORM instance, or None if not found.
        """
        entity = ParkingLotRepository.get_by_id(db, parking_lot_id)
        if entity is None:
            return None

        updates = data.model_dump(exclude_unset=True)
        if "title" in updates and updates["title"] is not None:
            updates["title"] = updates["title"].strip()
        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, parking_lot_id: int) -> bool:
        """
        Delete a parking lot item by identifier.

        Args:
            db: Active SQLAlchemy session.
            parking_lot_id: Primary key of the parking lot item.

        Returns:
            True if deleted, False if the item was not found.
        """
        entity = ParkingLotRepository.get_by_id(db, parking_lot_id)
        if entity is None:
            return False

        db.delete(entity)
        db.commit()
        return True
