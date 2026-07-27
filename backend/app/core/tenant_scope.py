"""Tenant (company) scoping helpers for multi-tenant isolation.

A user can only see data belonging to their own company and that
company's descendants in the tenant tree. Global administrators
(role == "global_admin" or a company with is_global=True) can see
everything.
"""

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.models.db.company import Company
from app.models.db.user import User


def get_accessible_company_ids(user: User, db: Session) -> list[int] | None:
    """Return the list of company ids a user may access.

    Returns None to mean "all companies" (global admin). Otherwise returns
    the user's company id plus all descendant company ids.
    """
    is_global = user.role == "global_admin"
    if is_global:
        return None

    if user.company_id is None:
        # Non-global user with no company: sees nothing.
        return []

    # Build the full tree once, then collect descendants of the root.
    companies = db.scalars(select(Company)).all()
    by_id = {c.id: c for c in companies}
    children: dict[int, list[int]] = {}
    for c in companies:
        parent = c.parent_id
        children.setdefault(parent, []).append(c.id)

    accessible: list[int] = []
    stack = [user.company_id]
    seen = set()
    while stack:
        cid = stack.pop()
        if cid in seen:
            continue
        seen.add(cid)
        accessible.append(cid)
        for child in children.get(cid, []):
            if child not in seen:
                stack.append(child)
    return accessible


class CompanyScope:
    """Resolved set of company ids the current user may access.

    `company_ids` is None when the user is a global admin (sees all).
    """

    def __init__(self, company_ids: list[int] | None) -> None:
        self.company_ids = company_ids

    @property
    def is_global(self) -> bool:
        return self.company_ids is None

    def filter(self, query, model):
        """Apply a company_id filter to a SQLAlchemy query if not global."""
        if self.company_ids is None:
            return query
        return query.where(model.company_id.in_(self.company_ids))


def get_company_scope(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyScope:
    return CompanyScope(get_accessible_company_ids(user, db))
