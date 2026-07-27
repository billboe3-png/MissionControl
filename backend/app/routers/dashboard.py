"""
Mission Control Dashboard Router

Sprint:
    0.1.1 - Dashboard Foundation
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.core.tenant_scope import CompanyScope, get_company_scope
from app.db import get_db
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/dashboard",
    summary="Mission Control Dashboard",
    response_description="Mission Control dashboard data",
)
async def get_dashboard(
    db: Session = Depends(get_db),
    scope: CompanyScope = Depends(get_company_scope),
):
    """Return the primary Mission Control dashboard payload.

    Global admins see all data; tenant users see only their company tree.
    """
    return await dashboard_service.get_dashboard(db, scope.company_ids)
