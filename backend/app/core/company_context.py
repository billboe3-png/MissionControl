"""
Mission Control Company Context

Provides company/site context to all routes via FastAPI dependency injection.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.

Scope always derives from the authenticated user's JWT claims, never from
client-supplied headers.

Usage:
    @router.get("/things")
    def list_things(ctx: CompanyContext = Depends(get_company_ctx)):
        things = repository.get_all(db, ctx.company_id, ctx.site_id)
"""

from dataclasses import dataclass

from fastapi import Depends

from app.core.auth_dependency import get_current_user
from app.models.db.user import User


@dataclass
class CompanyContext:
    """Tenant context derived from the authenticated user."""

    company_id: int | None = None
    site_id: int | None = None
    is_global: bool = False


async def get_company_ctx(
    current_user: User = Depends(get_current_user),
) -> CompanyContext:
    """
    Derive company/site context from the authenticated user's JWT claims.

    Global administrators see all companies (is_global=True). Non-global
    users are confined to their own company_id / site_id when querying.
    """
    return CompanyContext(
        company_id=current_user.company_id,
        site_id=current_user.site_id,
        is_global=current_user.role == "global_admin",
    )