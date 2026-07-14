"""
Mission Control Zabbix Router

API endpoints for Zabbix monitoring operations.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

import logging

from fastapi import APIRouter

from app.schemas.zabbix import (
    ZabbixConnectionTestResponse,
    ZabbixDashboardsResponse,
    ZabbixEventsResponse,
    ZabbixHealthResponse,
    ZabbixHostGroupsResponse,
    ZabbixHostsResponse,
    ZabbixItemsResponse,
    ZabbixMapsResponse,
    ZabbixProblemsResponse,
    ZabbixSummaryResponse,
    ZabbixTemplatesResponse,
    ZabbixTriggersResponse,
)
from app.services.zabbix_service import zabbix_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zabbix", tags=["zabbix"])


@router.get(
    "/overview",
    response_model=ZabbixSummaryResponse,
    tags=["zabbix"],
)
async def get_zabbix_overview() -> ZabbixSummaryResponse:
    """Get Zabbix monitoring overview."""
    data = await zabbix_service.get_summary()
    return ZabbixSummaryResponse(**data)


@router.get(
    "/hosts",
    response_model=ZabbixHostsResponse,
    tags=["zabbix"],
)
async def get_zabbix_hosts() -> ZabbixHostsResponse:
    """List monitored hosts."""
    data = await zabbix_service.get_hosts()
    return ZabbixHostsResponse(**data)


@router.get(
    "/groups",
    response_model=ZabbixHostGroupsResponse,
    tags=["zabbix"],
)
async def get_zabbix_groups() -> ZabbixHostGroupsResponse:
    """List host groups."""
    data = await zabbix_service.get_host_groups()
    return ZabbixHostGroupsResponse(**data)


@router.get(
    "/templates",
    response_model=ZabbixTemplatesResponse,
    tags=["zabbix"],
)
async def get_zabbix_templates() -> ZabbixTemplatesResponse:
    """List templates."""
    data = await zabbix_service.get_templates()
    return ZabbixTemplatesResponse(**data)


@router.get(
    "/items",
    response_model=ZabbixItemsResponse,
    tags=["zabbix"],
)
async def get_zabbix_items() -> ZabbixItemsResponse:
    """List items."""
    data = await zabbix_service.get_items()
    return ZabbixItemsResponse(**data)


@router.get(
    "/triggers",
    response_model=ZabbixTriggersResponse,
    tags=["zabbix"],
)
async def get_zabbix_triggers() -> ZabbixTriggersResponse:
    """List triggers."""
    data = await zabbix_service.get_triggers()
    return ZabbixTriggersResponse(**data)


@router.get(
    "/problems",
    response_model=ZabbixProblemsResponse,
    tags=["zabbix"],
)
async def get_zabbix_problems() -> ZabbixProblemsResponse:
    """List current problems."""
    data = await zabbix_service.get_problems()
    return ZabbixProblemsResponse(**data)


@router.get(
    "/events",
    response_model=ZabbixEventsResponse,
    tags=["zabbix"],
)
async def get_zabbix_events() -> ZabbixEventsResponse:
    """List recent events."""
    data = await zabbix_service.get_events()
    return ZabbixEventsResponse(**data)


@router.get(
    "/maps",
    response_model=ZabbixMapsResponse,
    tags=["zabbix"],
)
async def get_zabbix_maps() -> ZabbixMapsResponse:
    """List maps."""
    data = await zabbix_service.get_maps()
    return ZabbixMapsResponse(**data)


@router.get(
    "/dashboards",
    response_model=ZabbixDashboardsResponse,
    tags=["zabbix"],
)
async def get_zabbix_dashboards() -> ZabbixDashboardsResponse:
    """List dashboards."""
    data = await zabbix_service.get_dashboards()
    return ZabbixDashboardsResponse(**data)


@router.get(
    "/health",
    response_model=ZabbixHealthResponse,
    tags=["zabbix"],
)
async def get_zabbix_health() -> ZabbixHealthResponse:
    """Get Zabbix health."""
    data = await zabbix_service.get_health()
    return ZabbixHealthResponse(**data)


@router.post(
    "/test",
    response_model=ZabbixConnectionTestResponse,
    tags=["zabbix"],
)
async def test_zabbix_connection() -> ZabbixConnectionTestResponse:
    """Test connectivity to Zabbix."""
    data = await zabbix_service.test_connection()
    return ZabbixConnectionTestResponse(**data)
