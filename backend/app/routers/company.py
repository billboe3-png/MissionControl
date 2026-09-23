"""
Mission Control Company Router

REST API endpoints for company management.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.models.db.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
)
from app.services.auth_service import require_role
from app.services.company_service import CompanyService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[CompanyResponse])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return companies visible to the current user with stats."""
    result = CompanyService.get_all(db)
    if current_user.role != "global_admin":
        return [c for c in result.items if c.id == current_user.company_id]
    return result.items


@router.get("/summary")
def list_companies_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return lightweight company list for dropdowns."""
    if current_user.role != "global_admin":
        if current_user.company_id is None:
            return []
        companies = CompanyService.get_all(db).items
        return [
            c for c in companies if c.id == current_user.company_id
        ]
    return CompanyService.get_all_summary(db)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a single company by ID."""
    if (
        current_user.role != "global_admin"
        and company_id != current_user.company_id
    ):
        raise HTTPException(status_code=404, detail="Company not found")
    company = CompanyService.get_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("", response_model=CompanyResponse, status_code=201)
def create_company(
    request: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new company (global admins only)."""
    require_role(current_user, "global_admin")
    return CompanyService.create(db, request)


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    request: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing company (global admins only)."""
    require_role(current_user, "global_admin")
    company = CompanyService.update(db, company_id, request)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a company (global admins only)."""
    require_role(current_user, "global_admin")
    success = CompanyService.delete(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"status": "ok"}
