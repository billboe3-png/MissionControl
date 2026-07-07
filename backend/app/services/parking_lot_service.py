"""
Mission Control Parking Lot Service
"""


class ParkingLotService:
    """Parking lot dashboard section."""

    async def get_data(self) -> dict:

        return {
            "count": 0,
            "items": [],
        }


parking_lot_service = ParkingLotService()
