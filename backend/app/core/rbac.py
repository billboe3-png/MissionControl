"""
Mission Control RBAC & Tenancy Helpers

Centralized authorization helpers. Derives scope exclusively from the
authenticated user's JWT claims and reuses the role hierarchy defined in
app.services.auth_service.
"""

from collections.abc import Callable

from fastapi import Depends
from sqlalchemy import false, func, or_, select
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.models.db.company import Company
from app.models.db.user import User
from app.services.auth_service import require_role


def require_min_role(min_role: str) -> Callable[..., User]:
    """FastAPI dependency factory requiring at least `min_role` from the
    resolved current user."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        require_role(current_user, min_role)
        return current_user

    return dependency


def company_scope_clause(
    db: Session,
    user: User,
    model,
):
    """
    Build a SQLAlchemy filter clause scoping `model` (which must expose a
    `company_id` column) to the current user's company.

    Returns None for global admins (no filtering). Non-global users are
    confined to their own company. Legacy entities whose company_id is NULL
    remain visible as long as at most one company is configured (single-tenant
    production); otherwise NULL entities are treated as orphans visible only to
    global admins.
    """
    if user.role == "global_admin":
        return None
    if user.company_id is None:
        return false()

    clause = model.company_id == user.company_id
    if _is_single_company(db):
        clause = or_(clause, model.company_id.is_(None))
    return clause


def entity_in_company_scope(
    db: Session,
    user: User,
    company_id: int | None,
) -> bool:
    """True if an entity with the given company_id is visible to `user`."""
    if user.role == "global_admin":
        return True
    if user.company_id is None:
        return False
    if company_id == user.company_id:
        return True
    return company_id is None and _is_single_company(db)


def _is_single_company(db: Session) -> bool:
    count = db.scalar(select(func.count(Company.id))) or 0
    return count <= 1