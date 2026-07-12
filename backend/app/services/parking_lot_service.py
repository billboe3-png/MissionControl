"""
Mission Control Parking Lot Service

Business logic for the Parking Lot dashboard section.

Sprint:
    1.6.0
"""

import logging

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.models.db.parking_lot import ParkingLot
from app.repositories.parking_lot_repository import ParkingLotRepository
from app.schemas.parking_lot import ParkingLotCreate
from app.schemas.parking_lot import ParkingLotListResponse
from app.schemas.parking_lot import ParkingLotResponse
from app.schemas.parking_lot import ParkingLotUpdate

logger = logging.getLogger(__name__)


class ParkingLotService:
    """Parking lot dashboard section."""

    def __init__(self, repository: ParkingLotRepository | None = None) -> None:
        self._repository = repository or ParkingLotRepository()

    async def get_all(self, db: Session) -> ParkingLotListResponse:
        """Return all parking lot items as API response models."""
        logger.info("Fetching parking lot items")
        items = self._repository.get_all(db)
        response_items = [
            ParkingLotResponse.model_validate(item) for item in items
        ]
        return ParkingLotListResponse(count=len(response_items), items=response_items)

    async def get_by_id(self, db: Session, parking_lot_id: int) -> ParkingLotResponse:
        """Return a single parking lot item as an API response model."""
        logger.info("Fetching parking lot item id=%s", parking_lot_id)
        item = self._repository.get_by_id(db, parking_lot_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking lot item not found",
            )
        return ParkingLotResponse.model_validate(item)

    async def create(self, db: Session, data: ParkingLotCreate) -> ParkingLotResponse:
        """Create a new parking lot item and return the API response model."""
        logger.info("Creating parking lot item: %s", data.title)
        item = self._repository.create(db, data)
        return ParkingLotResponse.model_validate(item)

    async def update(
        self,
        db: Session,
        parking_lot_id: int,
        data: ParkingLotUpdate,
    ) -> ParkingLotResponse:
        """Update an existing parking lot item and return the API response model."""
        logger.info("Updating parking lot item id=%s", parking_lot_id)
        existing = self._repository.get_by_id(db, parking_lot_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking lot item not found",
            )
        updated = self._repository.update(db, parking_lot_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking lot item not found",
            )
        return ParkingLotResponse.model_validate(updated)

    async def delete(self, db: Session, parking_lot_id: int) -> None:
        """Delete a parking lot item by identifier."""
        logger.info("Deleting parking lot item id=%s", parking_lot_id)
        deleted = self._repository.delete(db, parking_lot_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking lot item not found",
            )

    async def get_data(self, db: Session) -> dict:
        """
        Return parking lot count and items loaded from PostgreSQL.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Dashboard parking lot payload with count and serialized items.
        """
        count = self._repository.get_count(db)
        items = self._repository.get_all(db)

        return {
            "count": count,
            "items": [self._serialize_item(item) for item in items],
        }

    @staticmethod
    def _serialize_item(item: ParkingLot) -> dict:
        """
        Map a ParkingLot ORM instance to the dashboard item shape.
        """
        return {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "priority": item.priority,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }


parking_lot_service = ParkingLotService()
