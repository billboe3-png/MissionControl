"""
Mission Control Identity Router

API endpoints for Active Directory and Microsoft 365
identity operations.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.identity import (
    ADActionResponse,
    ADDomainProfile,
    ADDevicesResponse,
    ADGroupMembershipRequest,
    ADGroupsResponse,
    ADHealthResponse,
    ADPasswordResetRequest,
    ADRenameRequest,
    ADSummaryResponse,
    ADUnlockRequest,
    ADUserGroupsResponse,
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

router = APIRouter(
    prefix="/identity",
    tags=["identity"],
    dependencies=[Depends(get_current_user)],
)


# ------------------------------------------------------------------ #
# Combined Overview                                                   #
# ------------------------------------------------------------------ #


@router.get("/overview", response_model=IdentityOverviewResponse)
async def get_identity_overview(db: Session = Depends(get_db)) -> IdentityOverviewResponse:
    """Get combined identity overview for the dashboard."""
    data = await identity_service.get_overview(db)
    return IdentityOverviewResponse(**data)


# ------------------------------------------------------------------ #
# Active Directory Endpoints                                          #
# ------------------------------------------------------------------ #


@router.get(
    "/ad/domains",
    response_model=list[ADDomainProfile],
    tags=["identity", "ad"],
)
async def ad_list_domains(
    db: Session = Depends(get_db),
) -> list[ADDomainProfile]:
    """List all configured AD domains for switching."""
    from app.repositories.integration_profile_repository import (
        IntegrationProfileRepository,
    )

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(
        db, "active_directory"
    )
    return [
        ADDomainProfile(
            id=p.id,
            name=p.name,
            domain=p.domain,
            base_dn=p.base_dn,
            enabled=p.enabled,
        )
        for p in profiles
    ]


@router.get(
    "/ad/test",
    response_model=ConnectionTestResponse,
    tags=["identity", "ad"],
)
async def ad_test_connection(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    """Test connectivity to Active Directory."""
    data = await identity_service.ad_test_connection(db, profile_id)
    return ConnectionTestResponse(**data)


@router.get(
    "/ad/summary",
    response_model=ADSummaryResponse,
    tags=["identity", "ad"],
)
async def ad_get_summary(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADSummaryResponse:
    """Get AD domain and forest summary."""
    data = await identity_service.ad_get_summary(db, profile_id)
    return ADSummaryResponse(**data)


@router.get(
    "/ad/users",
    response_model=ADUsersResponse,
    tags=["identity", "ad"],
)
async def ad_get_users(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADUsersResponse:
    """List Active Directory users."""
    data = await identity_service.ad_get_users(db, profile_id)
    return ADUsersResponse(**data)


@router.get(
    "/ad/groups",
    response_model=ADGroupsResponse,
    tags=["identity", "ad"],
)
async def ad_get_groups(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADGroupsResponse:
    """List Active Directory groups."""
    data = await identity_service.ad_get_groups(db, profile_id)
    return ADGroupsResponse(**data)


@router.get(
    "/ad/devices",
    response_model=ADDevicesResponse,
    tags=["identity", "ad"],
)
async def ad_get_devices(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADDevicesResponse:
    """List Active Directory computers/devices."""
    data = await identity_service.ad_get_devices(db, profile_id)
    return ADDevicesResponse(**data)


@router.get(
    "/ad/health",
    response_model=ADHealthResponse,
    tags=["identity", "ad"],
)
async def ad_get_health(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADHealthResponse:
    """Get AD health and replication status."""
    data = await identity_service.ad_get_health(db, profile_id)
    return ADHealthResponse(**data)


@router.post(
    "/ad/users/reset-password",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_reset_password(
    req: ADPasswordResetRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Reset a user's Active Directory password."""
    data = await identity_service.ad_reset_password(
        db, req.sam_account_name, req.new_password, profile_id
    )
    return ADActionResponse(**data)


@router.post(
    "/ad/users/unlock",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_unlock_account(
    req: ADUnlockRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Unlock a locked Active Directory account."""
    data = await identity_service.ad_unlock_account(db, req.sam_account_name, profile_id)
    return ADActionResponse(**data)


@router.post(
    "/ad/users/enable",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_enable_account(
    req: ADUnlockRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Enable a disabled Active Directory account."""
    data = await identity_service.ad_enable_account(db, req.sam_account_name, profile_id)
    return ADActionResponse(**data)


@router.post(
    "/ad/users/disable",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_disable_account(
    req: ADUnlockRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Disable an Active Directory account."""
    data = await identity_service.ad_disable_account(db, req.sam_account_name, profile_id)
    return ADActionResponse(**data)


@router.post(
    "/ad/users/rename",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_rename_user(
    req: ADRenameRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Rename an Active Directory user."""
    data = await identity_service.ad_rename_user(
        db, req.sam_account_name, req.display_name, req.first_name, req.last_name, profile_id
    )
    return ADActionResponse(**data)


@router.get(
    "/ad/users/{sam_account_name}/groups",
    response_model=ADUserGroupsResponse,
    tags=["identity", "ad"],
)
async def ad_get_user_groups(
    sam_account_name: str,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADUserGroupsResponse:
    """Get groups that a user belongs to."""
    data = await identity_service.ad_get_user_groups(db, sam_account_name, profile_id)
    return ADUserGroupsResponse(**data)


@router.post(
    "/ad/users/add-to-group",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_add_to_group(
    req: ADGroupMembershipRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Add a user to an Active Directory group."""
    data = await identity_service.ad_add_to_group(
        db, req.sam_account_name, req.group_name, profile_id
    )
    return ADActionResponse(**data)


@router.post(
    "/ad/users/remove-from-group",
    response_model=ADActionResponse,
    tags=["identity", "ad"],
)
async def ad_remove_from_group(
    req: ADGroupMembershipRequest,
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ADActionResponse:
    """Remove a user from an Active Directory group."""
    data = await identity_service.ad_remove_from_group(
        db, req.sam_account_name, req.group_name, profile_id
    )
    return ADActionResponse(**data)


# ------------------------------------------------------------------ #
# Microsoft 365 Endpoints                                             #
# ------------------------------------------------------------------ #


@router.get(
    "/m365/domains",
    response_model=list[ADDomainProfile],
    tags=["identity", "m365"],
)
async def m365_list_domains(
    db: Session = Depends(get_db),
) -> list[ADDomainProfile]:
    """List all configured Microsoft 365 tenant profiles for switching."""
    from app.repositories.integration_profile_repository import (
        IntegrationProfileRepository,
    )

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(
        db, "microsoft_365"
    )
    return [
        ADDomainProfile(
            id=p.id,
            name=p.name,
            domain=p.tenant_id,
            base_dn=None,
            enabled=p.enabled,
        )
        for p in profiles
    ]


@router.get(
    "/m365/test",
    response_model=ConnectionTestResponse,
    tags=["identity", "m365"],
)
async def m365_test_connection(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    """Test connectivity to Microsoft 365."""
    data = await identity_service.m365_test_connection(db, profile_id)
    return ConnectionTestResponse(**data)


@router.get(
    "/m365/summary",
    response_model=M365SummaryResponse,
    tags=["identity", "m365"],
)
async def m365_get_summary(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> M365SummaryResponse:
    """Get Microsoft 365 tenant summary."""
    data = await identity_service.m365_get_summary(db, profile_id)
    return M365SummaryResponse(**data)


@router.get(
    "/m365/users",
    response_model=M365UsersResponse,
    tags=["identity", "m365"],
)
async def m365_get_users(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> M365UsersResponse:
    """List Microsoft 365 users."""
    data = await identity_service.m365_get_users(db, profile_id)
    return M365UsersResponse(**data)


@router.get(
    "/m365/groups",
    response_model=M365GroupsResponse,
    tags=["identity", "m365"],
)
async def m365_get_groups(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> M365GroupsResponse:
    """List Microsoft 365 groups."""
    data = await identity_service.m365_get_groups(db, profile_id)
    return M365GroupsResponse(**data)


@router.get(
    "/m365/devices",
    response_model=M365DevicesResponse,
    tags=["identity", "m365"],
)
async def m365_get_devices(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> M365DevicesResponse:
    """List Microsoft 365 managed devices."""
    data = await identity_service.m365_get_devices(db, profile_id)
    return M365DevicesResponse(**data)


@router.get(
    "/m365/health",
    response_model=M365HealthResponse,
    tags=["identity", "m365"],
)
async def m365_get_health(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
) -> M365HealthResponse:
    """Get Microsoft 365 service health."""
    data = await identity_service.m365_get_health(db, profile_id)
    return M365HealthResponse(**data)
