"""
Mission Control Zabbix Router

API endpoints for Zabbix monitoring operations.

Sprint 2.3.0 - Enterprise Zabbix Integration.
Sprint 2.3.2 - DB-driven provider resolution.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
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
async def get_zabbix_overview(
    db: Session = Depends(get_db),
) -> ZabbixSummaryResponse:
    """Get Zabbix monitoring overview."""
    data = await zabbix_service.get_summary(db)
    return ZabbixSummaryResponse(**data)


@router.get(
    "/hosts",
    response_model=ZabbixHostsResponse,
    tags=["zabbix"],
)
async def get_zabbix_hosts(
    db: Session = Depends(get_db),
) -> ZabbixHostsResponse:
    """List monitored hosts."""
    data = await zabbix_service.get_hosts(db)
    return ZabbixHostsResponse(**data)


@router.get(
    "/groups",
    response_model=ZabbixHostGroupsResponse,
    tags=["zabbix"],
)
async def get_zabbix_groups(
    db: Session = Depends(get_db),
) -> ZabbixHostGroupsResponse:
    """List host groups."""
    data = await zabbix_service.get_host_groups(db)
    return ZabbixHostGroupsResponse(**data)


@router.get(
    "/templates",
    response_model=ZabbixTemplatesResponse,
    tags=["zabbix"],
)
async def get_zabbix_templates(
    db: Session = Depends(get_db),
) -> ZabbixTemplatesResponse:
    """List templates."""
    data = await zabbix_service.get_templates(db)
    return ZabbixTemplatesResponse(**data)


@router.get(
    "/items",
    response_model=ZabbixItemsResponse,
    tags=["zabbix"],
)
async def get_zabbix_items(
    db: Session = Depends(get_db),
) -> ZabbixItemsResponse:
    """List items."""
    data = await zabbix_service.get_items(db)
    return ZabbixItemsResponse(**data)


@router.get(
    "/triggers",
    response_model=ZabbixTriggersResponse,
    tags=["zabbix"],
)
async def get_zabbix_triggers(
    db: Session = Depends(get_db),
) -> ZabbixTriggersResponse:
    """List triggers."""
    data = await zabbix_service.get_triggers(db)
    return ZabbixTriggersResponse(**data)


@router.get(
    "/problems",
    response_model=ZabbixProblemsResponse,
    tags=["zabbix"],
)
async def get_zabbix_problems(
    db: Session = Depends(get_db),
) -> ZabbixProblemsResponse:
    """List current problems."""
    data = await zabbix_service.get_problems(db)
    return ZabbixProblemsResponse(**data)


@router.get(
    "/events",
    response_model=ZabbixEventsResponse,
    tags=["zabbix"],
)
async def get_zabbix_events(
    db: Session = Depends(get_db),
) -> ZabbixEventsResponse:
    """List recent events."""
    data = await zabbix_service.get_events(db)
    return ZabbixEventsResponse(**data)


@router.get(
    "/maps",
    response_model=ZabbixMapsResponse,
    tags=["zabbix"],
)
async def get_zabbix_maps(
    db: Session = Depends(get_db),
) -> ZabbixMapsResponse:
    """List maps."""
    data = await zabbix_service.get_maps(db)
    return ZabbixMapsResponse(**data)


@router.get(
    "/dashboards",
    response_model=ZabbixDashboardsResponse,
    tags=["zabbix"],
)
async def get_zabbix_dashboards(
    db: Session = Depends(get_db),
) -> ZabbixDashboardsResponse:
    """List dashboards."""
    data = await zabbix_service.get_dashboards(db)
    return ZabbixDashboardsResponse(**data)


@router.get(
    "/health",
    response_model=ZabbixHealthResponse,
    tags=["zabbix"],
)
async def get_zabbix_health(
    db: Session = Depends(get_db),
) -> ZabbixHealthResponse:
    """Get Zabbix health."""
    data = await zabbix_service.get_health(db)
    return ZabbixHealthResponse(**data)


@router.post(
    "/test",
    response_model=ZabbixConnectionTestResponse,
    tags=["zabbix"],
)
async def test_zabbix_connection(
    db: Session = Depends(get_db),
) -> ZabbixConnectionTestResponse:
    """Test connectivity to Zabbix."""
    data = await zabbix_service.test_connection(db)
    return ZabbixConnectionTestResponse(**data)
