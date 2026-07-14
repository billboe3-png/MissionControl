"""
Mission Control Identity Router

API endpoints for Active Directory and Microsoft 365
identity operations.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging

from fastapi import APIRouter

from app.schemas.identity import (
    ADDevicesResponse,
    ADGroupsResponse,
    ADHealthResponse,
    ADSummaryResponse,
    ADUsersResponse,
    ConnectionTestResponse,
    IdentityOverviewResponse,
    M365DevicesResponse,
    M365GroupsResponse,
    M365HealthResponse,
    M365SummaryResponse,
    M365UsersResponse,
)
from app.services.identity_service import identity_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/identity", tags=["identity"])


# ------------------------------------------------------------------ #
# Combined Overview                                                   #
# ------------------------------------------------------------------ #


@router.get("/overview", response_model=IdentityOverviewResponse)
async def get_identity_overview() -> IdentityOverviewResponse:
    """Get combined identity overview for the dashboard."""
    data = await identity_service.get_overview()
    return IdentityOverviewResponse(**data)


# ------------------------------------------------------------------ #
# Active Directory Endpoints                                          #
# ------------------------------------------------------------------ #


@router.get(
    "/ad/test",
    response_model=ConnectionTestResponse,
    tags=["identity", "ad"],
)
async def ad_test_connection() -> ConnectionTestResponse:
    """Test connectivity to Active Directory."""
    data = await identity_service.ad_test_connection()
    return ConnectionTestResponse(**data)


@router.get(
    "/ad/summary",
    response_model=ADSummaryResponse,
    tags=["identity", "ad"],
)
async def ad_get_summary() -> ADSummaryResponse:
    """Get AD domain and forest summary."""
    data = await identity_service.ad_get_summary()
    return ADSummaryResponse(**data)


@router.get(
    "/ad/users",
    response_model=ADUsersResponse,
    tags=["identity", "ad"],
)
async def ad_get_users() -> ADUsersResponse:
    """List Active Directory users."""
    data = await identity_service.ad_get_users()
    return ADUsersResponse(**data)


@router.get(
    "/ad/groups",
    response_model=ADGroupsResponse,
    tags=["identity", "ad"],
)
async def ad_get_groups() -> ADGroupsResponse:
    """List Active Directory groups."""
    data = await identity_service.ad_get_groups()
    return ADGroupsResponse(**data)


@router.get(
    "/ad/devices",
    response_model=ADDevicesResponse,
    tags=["identity", "ad"],
)
async def ad_get_devices() -> ADDevicesResponse:
    """List Active Directory computers/devices."""
    data = await identity_service.ad_get_devices()
    return ADDevicesResponse(**data)


@router.get(
    "/ad/health",
    response_model=ADHealthResponse,
    tags=["identity", "ad"],
)
async def ad_get_health() -> ADHealthResponse:
    """Get AD health and replication status."""
    data = await identity_service.ad_get_health()
    return ADHealthResponse(**data)


# ------------------------------------------------------------------ #
# Microsoft 365 Endpoints                                             #
# ------------------------------------------------------------------ #


@router.get(
    "/m365/test",
    response_model=ConnectionTestResponse,
    tags=["identity", "m365"],
)
async def m365_test_connection() -> ConnectionTestResponse:
    """Test connectivity to Microsoft 365."""
    data = await identity_service.m365_test_connection()
    return ConnectionTestResponse(**data)


@router.get(
    "/m365/summary",
    response_model=M365SummaryResponse,
    tags=["identity", "m365"],
)
async def m365_get_summary() -> M365SummaryResponse:
    """Get Microsoft 365 tenant summary."""
    data = await identity_service.m365_get_summary()
    return M365SummaryResponse(**data)


@router.get(
    "/m365/users",
    response_model=M365UsersResponse,
    tags=["identity", "m365"],
)
async def m365_get_users() -> M365UsersResponse:
    """List Microsoft 365 users."""
    data = await identity_service.m365_get_users()
    return M365UsersResponse(**data)


@router.get(
    "/m365/groups",
    response_model=M365GroupsResponse,
    tags=["identity", "m365"],
)
async def m365_get_groups() -> M365GroupsResponse:
    """List Microsoft 365 groups."""
    data = await identity_service.m365_get_groups()
    return M365GroupsResponse(**data)


@router.get(
    "/m365/devices",
    response_model=M365DevicesResponse,
    tags=["identity", "m365"],
)
async def m365_get_devices() -> M365DevicesResponse:
    """List Microsoft 365 managed devices."""
    data = await identity_service.m365_get_devices()
    return M365DevicesResponse(**data)


@router.get(
    "/m365/health",
    response_model=M365HealthResponse,
    tags=["identity", "m365"],
)
async def m365_get_health() -> M365HealthResponse:
    """Get Microsoft 365 service health."""
    data = await identity_service.m365_get_health()
    return M365HealthResponse(**data)
