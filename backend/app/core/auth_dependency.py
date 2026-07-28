"""
Mission Control Auth Dependency

FastAPI dependency that extracts and validates the current user from the
Authorization header.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.db.user import User
from app.services.auth_service import AuthService


async def get_current_user(
    authorization: str | None = Header(None),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract the current user from the Authorization header (HTTP) or a
    `token` query parameter (WebSocket handshakes, where browsers cannot
    send custom headers).

    Expects: Authorization: Bearer <token>   OR   ?token=<token>
    """
    raw = None
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            raw = parts[1]
    if raw is None and token:
        raw = token

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or token query parameter",
        )

    try:
        return AuthService.get_current_user(db, raw)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from err
