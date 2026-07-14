"""
Mission Control Integration Router

API endpoints for managing external integration profiles.

Sprint 2.3.1 - Integration Management (Production Configuration UI).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.integration import (
    IntegrationProfileCreate,
    IntegrationProfileListResponse,
    IntegrationProfileResponse,
    IntegrationProfileUpdate,
    IntegrationTestResponse,
)
from app.services.integration_service import (
    IntegrationService,
    integration_service,
)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


def get_integration_service() -> IntegrationService:
    return integration_service


# ------------------------------------------------------------------ #
# CRUD                                                                #
# ------------------------------------------------------------------ #


@router.get(
    "", response_model=IntegrationProfileListResponse
)
async def list_integrations(
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationProfileListResponse:
    return await service.list_profiles(db)


@router.get(
    "/{profile_id}",
    response_model=IntegrationProfileResponse,
)
async def get_integration(
    profile_id: int,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationProfileResponse:
    return await service.get_profile(db, profile_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IntegrationProfileResponse,
)
async def create_integration(
    payload: IntegrationProfileCreate,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationProfileResponse:
    return await service.create_profile(db, payload)


@router.put(
    "/{profile_id}",
    response_model=IntegrationProfileResponse,
)
async def update_integration(
    profile_id: int,
    payload: IntegrationProfileUpdate,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationProfileResponse:
    return await service.update_profile(db, profile_id, payload)


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_integration(
    profile_id: int,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> None:
    await service.delete_profile(db, profile_id)


# ------------------------------------------------------------------ #
# Actions                                                             #
# ------------------------------------------------------------------ #


@router.post(
    "/{profile_id}/test",
    response_model=IntegrationTestResponse,
)
async def test_integration(
    profile_id: int,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationTestResponse:
    return await service.test_connection(db, profile_id)


@router.post(
    "/{profile_id}/enable",
    response_model=IntegrationProfileResponse,
)
async def enable_integration(
    profile_id: int,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationProfileResponse:
    return await service.enable_profile(db, profile_id)


@router.post(
    "/{profile_id}/disable",
    response_model=IntegrationProfileResponse,
)
async def disable_integration(
    profile_id: int,
    db: Session = Depends(get_db),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationProfileResponse:
    return await service.disable_profile(db, profile_id)
