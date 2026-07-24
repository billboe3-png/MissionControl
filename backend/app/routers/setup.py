"""
Mission Control Setup Router

Endpoints for first-time installation wizard.
Only functional when no users exist in the system.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.setup import (
    BootstrapRequest,
    BootstrapResponse,
    SetupStatusResponse,
)
from app.services.setup_service import bootstrap, is_setup_required

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setup", tags=["Setup"])


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(
    db: Session = Depends(get_db),
) -> SetupStatusResponse:
    """Check whether the setup wizard is required."""
    return SetupStatusResponse(setup_required=is_setup_required(db))


@router.post(
    "/bootstrap",
    response_model=BootstrapResponse,
    status_code=201,
)
async def run_bootstrap(
    payload: BootstrapRequest,
    db: Session = Depends(get_db),
) -> BootstrapResponse:
    """
    Create the first Company, Site, and Global Administrator.

    Only works when no users exist. After completion, the setup
    wizard is permanently disabled.
    """
    result = bootstrap(db, payload)
    return BootstrapResponse(**result)
