"""
Mission Control Identity Router

API endpoints for Active Directory and Microsoft 365
identity operations.

Sprint 2.2.1 - Identity Platform Foundation.
"""

import logging

from fastapi import APIRouter

from app.schemas.identity import (
    ComputerSummaryResponse,
    DHCPHealthResponse,
    DNSHealthResponse,
    DomainControllerResponse,
    DomainResponse,
    EntraHealthResponse,
    ExchangeHealthResponse,
    ForestResponse,
    FSMORoleResponse,
    GPOResponse,
    GroupSummaryResponse,
    IdentityOverviewResponse,
    LicenseSummaryResponse,
    MessageCenterResponse,
    OrganizationalUnitResponse,
    SecureScoreResponse,
    ServiceHealthResponse,
    TenantResponse,
    UserSummaryResponse,
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
    overview = data.get("overview", {})
    ad = overview.get("ad", {})
    m365 = overview.get("m365", {})

    return IdentityOverviewResponse(
        ad_domain_controllers=ad.get("domain_controllers", 0),
        ad_users_total=ad.get("total_users", 0),
        ad_computers_total=ad.get("total_computers", 0),
        ad_groups_total=ad.get("total_groups", 0),
        ad_gpos_total=ad.get("total_gpos", 0),
        m365_total_users=m365.get("total_users", 0),
        m365_licensed_users=m365.get("licensed_users", 0),
        m365_overall_status=m365.get("overall_status", "unknown"),
        m365_active_incidents=m365.get("active_incidents", 0),
        m365_secure_score=m365.get("secure_score", 0),
    )


# ------------------------------------------------------------------ #
# Active Directory Endpoints                                          #
# ------------------------------------------------------------------ #


@router.get("/ad/domain-controllers", response_model=DomainControllerResponse)
async def get_domain_controllers() -> DomainControllerResponse:
    """List domain controllers in the forest."""
    data = await identity_service.get_domain_controllers()
    return DomainControllerResponse(**data)


@router.get("/ad/forest", response_model=ForestResponse)
async def get_forest() -> ForestResponse:
    """Get forest information."""
    data = await identity_service.get_forest()
    return ForestResponse(**data)


@router.get("/ad/domain", response_model=DomainResponse)
async def get_domain() -> DomainResponse:
    """Get domain information."""
    data = await identity_service.get_domain()
    return DomainResponse(**data)


@router.get("/ad/ous", response_model=OrganizationalUnitResponse)
async def get_organizational_units() -> OrganizationalUnitResponse:
    """List organizational units."""
    data = await identity_service.get_organizational_units()
    return OrganizationalUnitResponse(**data)


@router.get("/ad/users", response_model=UserSummaryResponse)
async def get_users() -> UserSummaryResponse:
    """List user summaries."""
    data = await identity_service.get_users()
    return UserSummaryResponse(**data)


@router.get("/ad/groups", response_model=GroupSummaryResponse)
async def get_groups() -> GroupSummaryResponse:
    """List group summaries."""
    data = await identity_service.get_groups()
    return GroupSummaryResponse(**data)


@router.get("/ad/computers", response_model=ComputerSummaryResponse)
async def get_computers() -> ComputerSummaryResponse:
    """List computer summaries."""
    data = await identity_service.get_computers()
    return ComputerSummaryResponse(**data)


@router.get("/ad/gpos", response_model=GPOResponse)
async def get_gpos() -> GPOResponse:
    """List Group Policy Objects."""
    data = await identity_service.get_gpos()
    return GPOResponse(**data)


@router.get("/ad/fsmo-roles", response_model=FSMORoleResponse)
async def get_fsmo_roles() -> FSMORoleResponse:
    """Get FSMO role holders."""
    data = await identity_service.get_fsmo_roles()
    return FSMORoleResponse(
        success=data["success"],
        fsmo_roles={
            "forest_roles": data.get("forest_roles", {}),
            "domain_roles": data.get("domain_roles", {}),
            "all_roles_held_by_single_dc": data.get(
                "all_roles_held_by_single_dc", False
            ),
        },
    )


@router.get("/ad/dns-health", response_model=DNSHealthResponse)
async def get_dns_health() -> DNSHealthResponse:
    """Get DNS health status."""
    data = await identity_service.get_dns_health()
    return DNSHealthResponse(**data)


@router.get("/ad/dhcp-health", response_model=DHCPHealthResponse)
async def get_dhcp_health() -> DHCPHealthResponse:
    """Get DHCP health status."""
    data = await identity_service.get_dhcp_health()
    return DHCPHealthResponse(**data)


# ------------------------------------------------------------------ #
# Microsoft 365 Endpoints                                             #
# ------------------------------------------------------------------ #


@router.get("/m365/tenant", response_model=TenantResponse)
async def get_tenant() -> TenantResponse:
    """Get tenant information."""
    data = await identity_service.get_tenant()
    return TenantResponse(**data)


@router.get("/m365/licenses", response_model=LicenseSummaryResponse)
async def get_licenses() -> LicenseSummaryResponse:
    """List license summaries."""
    data = await identity_service.get_licenses()
    return LicenseSummaryResponse(**data)


@router.get("/m365/service-health", response_model=ServiceHealthResponse)
async def get_service_health() -> ServiceHealthResponse:
    """Get Microsoft 365 service health."""
    data = await identity_service.get_service_health()
    return ServiceHealthResponse(**data)


@router.get("/m365/entra-health", response_model=EntraHealthResponse)
async def get_entra_health() -> EntraHealthResponse:
    """Get Entra ID health."""
    data = await identity_service.get_entra_health()
    return EntraHealthResponse(**data)


@router.get("/m365/exchange-health", response_model=ExchangeHealthResponse)
async def get_exchange_health() -> ExchangeHealthResponse:
    """Get Exchange Online health."""
    data = await identity_service.get_exchange_health()
    return ExchangeHealthResponse(**data)


@router.get("/m365/secure-score", response_model=SecureScoreResponse)
async def get_secure_score() -> SecureScoreResponse:
    """Get Secure Score."""
    data = await identity_service.get_secure_score()
    return SecureScoreResponse(**data)


@router.get("/m365/message-center", response_model=MessageCenterResponse)
async def get_message_center() -> MessageCenterResponse:
    """Get Message Center items."""
    data = await identity_service.get_message_center()
    mc = data.get("message_center", data)
    return MessageCenterResponse(
        total_items=mc.get("total_items", 0),
        items=mc.get("items", []),
    )
