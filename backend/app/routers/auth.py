"""
Mission Control Auth Router

REST API endpoints for authentication and user management.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.core.tenant_scope import CompanyScope, get_company_scope
from app.db import get_db
from app.models.db.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    UserCreateRequest,
    UserResponse,
    UserSummary,
    UserUpdateRequest,
)
from app.services.auth_service import (
    AuthService,
    hash_password,
    require_role,
    verify_password,
)

logger = logging.getLogger(__name__)



router = APIRouter(prefix="/auth", tags=["Authentication"])


# ------------------------------------------------------------------ #
# Login                                                                #
# ------------------------------------------------------------------ #


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return an access token."""
    user, token = AuthService.authenticate(db, request.email, request.password)
    return LoginResponse(
        access_token=token,
        user=UserSummary(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            company_id=user.company_id,
            site_id=user.site_id,
            enabled=user.enabled,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        company_id=current_user.company_id,
        site_id=current_user.site_id,
        enabled=current_user.enabled,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
    )


@router.post("/change-password")
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    return {"status": "ok"}


# ------------------------------------------------------------------ #
# User Management (admin only)                                         #
# ------------------------------------------------------------------ #


@router.get("/users", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scope: CompanyScope = Depends(get_company_scope),
):
    """List users. Global admins see all; others see their tenant tree."""
    require_role(current_user, "company_admin")

    stmt = select(User).order_by(User.email.asc())

    if not scope.is_global:
        stmt = stmt.where(User.company_id.in_(scope.company_ids))

    users = db.scalars(stmt).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            company_id=u.company_id,
            site_id=u.site_id,
            enabled=u.enabled,
            last_login=u.last_login,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user. Company admins can only create within their company."""
    require_role(current_user, "company_admin")

    company_id = request.company_id
    if current_user.role != "global_admin":
        company_id = current_user.company_id

    user = AuthService.create_user(
        db,
        email=request.email,
        display_name=request.display_name,
        password=request.password,
        role=request.role,
        company_id=company_id,
        site_id=request.site_id,
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        company_id=user.company_id,
        site_id=user.site_id,
        enabled=user.enabled,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a user's role or status."""
    require_role(current_user, "company_admin")

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if request.display_name is not None:
        user.display_name = request.display_name
    if request.role is not None:
        user.role = request.role
    if request.enabled is not None:
        user.enabled = request.enabled
    if request.company_id is not None:
        user.company_id = request.company_id
    if request.site_id is not None:
        user.site_id = request.site_id

    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        company_id=user.company_id,
        site_id=user.site_id,
        enabled=user.enabled,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a user."""
    require_role(current_user, "company_admin")

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account",
        )

    db.delete(user)
    db.commit()
    return {"status": "ok"}
