"""
Mission Control Parking Lot Router

Sprint:
    1.6.0 - Parking Lot API Foundation
"""

import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.parking_lot import (
    ParkingLotCreate,
    ParkingLotListResponse,
    ParkingLotResponse,
    ParkingLotUpdate,
)
from app.services.parking_lot_service import ParkingLotService, parking_lot_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/parking-lot",
    tags=["Parking Lot"],
    dependencies=[Depends(get_current_user)],
)


def get_parking_lot_service() -> ParkingLotService:
    """Provide the shared parking lot service instance."""
    return parking_lot_service


@router.get(
    "",
    summary="List parking lot items",
    description="Return all parking lot items managed by Mission Control.",
    response_model=ParkingLotListResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Parking lot items retrieved successfully.",
            "model": ParkingLotListResponse,
        },
    },
)
async def list_parking_lot_items(
    db: Session = Depends(get_db),
    service: ParkingLotService = Depends(get_parking_lot_service),
) -> ParkingLotListResponse:
    return await service.get_all(db)


@router.get(
    "/{parking_lot_id}",
    summary="Get parking lot item",
    description="Return a single parking lot item by its identifier.",
    response_model=ParkingLotResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Parking lot item retrieved successfully.",
            "model": ParkingLotResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Parking lot item not found.",
        },
    },
)
async def get_parking_lot_item(
    parking_lot_id: int,
    db: Session = Depends(get_db),
    service: ParkingLotService = Depends(get_parking_lot_service),
) -> ParkingLotResponse:
    return await service.get_by_id(db, parking_lot_id)


@router.post(
    "",
    summary="Create parking lot item",
    description="Create a new parking lot item.",
    response_model=ParkingLotResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Parking lot item created successfully.",
            "model": ParkingLotResponse,
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def create_parking_lot_item(
    payload: ParkingLotCreate,
    db: Session = Depends(get_db),
    service: ParkingLotService = Depends(get_parking_lot_service),
) -> ParkingLotResponse:
    return await service.create(db, payload)


@router.put(
    "/{parking_lot_id}",
    summary="Update parking lot item",
    description="Update an existing parking lot item.",
    response_model=ParkingLotResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Parking lot item updated successfully.",
            "model": ParkingLotResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Parking lot item not found.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error.",
        },
    },
)
async def update_parking_lot_item(
    parking_lot_id: int,
    payload: ParkingLotUpdate,
    db: Session = Depends(get_db),
    service: ParkingLotService = Depends(get_parking_lot_service),
) -> ParkingLotResponse:
    return await service.update(db, parking_lot_id, payload)


@router.delete(
    "/{parking_lot_id}",
    summary="Delete parking lot item",
    description="Delete a parking lot item by its identifier.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Parking lot item deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Parking lot item not found.",
        },
    },
)
async def delete_parking_lot_item(
    parking_lot_id: int,
    db: Session = Depends(get_db),
    service: ParkingLotService = Depends(get_parking_lot_service),
) -> Response:
    await service.delete(db, parking_lot_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
