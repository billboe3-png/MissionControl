"""
Mission Control Auth Dependency

FastAPI dependency that extracts and validates the current user from the
Authorization header.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.db.user import User
from app.services.auth_service import AuthService


async def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract the current user from the Authorization header.

    Expects: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format (expected: Bearer <token>)",
        )

    try:
        return AuthService.get_current_user(db, parts[1])
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from err
