"""
Mission Control Company Context

Provides company/site context to all routes via FastAPI dependency injection.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.

Usage:
    @router.get("/things")
    def list_things(ctx: CompanyContext = Depends(get_company_ctx)):
        things = repository.get_all(db, ctx.company_id, ctx.site_id)
"""

import contextlib
from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.db import get_db


@dataclass
class CompanyContext:
    """Tenant context extracted from the current request."""

    company_id: int | None = None
    site_id: int | None = None
    is_global: bool = False


async def get_company_ctx(
    request: Request,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    x_site_id: str | None = Header(None, alias="X-Site-Id"),
    db: Session = Depends(get_db),
) -> CompanyContext:
    """
    Extract company/site context from request headers.

    Headers:
        X-Company-Id: The ID of the company to scope queries to.
        X-Site-Id: The ID of the site to scope queries to.

    Global administrators can omit X-Company-Id to see all companies.
    Regular users must always provide X-Company-Id.
    """
    company_id = None
    site_id = None
    is_global = False

    if x_company_id:
        with contextlib.suppress(ValueError):
            company_id = int(x_company_id)

    if x_site_id:
        with contextlib.suppress(ValueError):
            site_id = int(x_site_id)

    # Check if this is a global admin (future Phase 4 will use JWT)
    # For now, allow access without company_id for backward compatibility
    if company_id is None:
        is_global = True

    return CompanyContext(
        company_id=company_id,
        site_id=site_id,
        is_global=is_global,
    )
