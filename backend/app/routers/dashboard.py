"""
Mission Control Dashboard Router

Sprint:
    0.1.1 - Dashboard Foundation
"""

from fastapi import APIRouter

from app.services.dashboard_service import dashboard_service

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard",
    summary="Mission Control Dashboard",
    response_description="Mission Control dashboard data",
)
async def get_dashboard():
    """
    Return the primary Mission Control dashboard payload.

    This endpoint serves as the main data source for the frontend dashboard.
    Additional widgets will extend the payload in future sprints without
    changing the endpoint.
    """
    return await dashboard_service.get_dashboard()
