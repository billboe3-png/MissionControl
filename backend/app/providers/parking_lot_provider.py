"""
Mission Control Parking Lot Provider

Returns parking lot data for the dashboard.
Treats parking lot as a backlog.
"""

import logging

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.parking_lot import ParkingLot

logger = logging.getLogger(__name__)


class ParkingLotProvider:
    """Return parking lot data for the dashboard."""

    def get_parking_lot_data(self, db: Session) -> dict:
        """Return parking lot count, statistics, and items."""
        total = db.scalar(
            select(func.count()).select_from(ParkingLot)
        ) or 0

        parked = db.scalar(
            select(func.count()).select_from(ParkingLot).where(
                ParkingLot.status == "parked",
                ParkingLot.archived.is_(False),
            )
        ) or 0

        in_progress = db.scalar(
            select(func.count()).select_from(ParkingLot).where(
                ParkingLot.status == "in_progress",
                ParkingLot.archived.is_(False),
            )
        ) or 0

        done = db.scalar(
            select(func.count()).select_from(ParkingLot).where(
                ParkingLot.status == "done",
            )
        ) or 0

        archived = db.scalar(
            select(func.count()).select_from(ParkingLot).where(
                ParkingLot.archived.is_(True),
            )
        ) or 0

        items = (
            db.query(ParkingLot)
            .where(ParkingLot.archived.is_(False))
            .order_by(ParkingLot.updated_at.desc())
            .all()
        )

        return {
            "count": total,
            "statistics": {
                "total": total,
                "parked": parked,
                "in_progress": in_progress,
                "done": done,
                "archived": archived,
            },
            "items": [self._serialize(item) for item in items],
        }

    @staticmethod
    def _serialize(item: ParkingLot) -> dict:
        return {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "priority": item.priority,
            "status": item.status,
            "owner": item.owner,
            "category": item.category,
            "labels": item.labels,
            "target_sprint": item.target_sprint,
            "archived": item.archived,
            "created_by": item.created_by,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }


parking_lot_provider = ParkingLotProvider()
