"""
Mission Control Authentication Service

JWT-based authentication with company/site scoping.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.

Roles:
    global_admin  — Can view/switch all companies and sites
    company_admin — Can manage their company and all its sites
    site_admin    — Can manage assigned sites
    operator      — Can execute commands within assigned scope
    readonly      — Read-only access within assigned scope
"""

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db.user import User

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Role hierarchy                                                       #
# ------------------------------------------------------------------ #

ROLES = ["global_admin", "company_admin", "site_admin", "operator", "readonly"]

ROLE_HIERARCHY = {
    "global_admin": 5,
    "company_admin": 4,
    "site_admin": 3,
    "operator": 2,
    "readonly": 1,
}


def role_has_min_level(role: str, min_level: int) -> bool:
    """Check if a role meets the minimum authorization level."""
    return ROLE_HIERARCHY.get(role, 0) >= min_level


def require_role(user: User, min_role: str) -> None:
    """Raise 403 if user's role is below the required level."""
    if not role_has_min_level(user.role, ROLE_HIERARCHY.get(min_role, 0)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires at least {min_role} role",
        )


# ------------------------------------------------------------------ #
# Password hashing                                                     #
# ------------------------------------------------------------------ #

_SALT_PREFIX = "mc_"


def hash_password(password: str) -> str:
    """Hash a password with a per-user salt using PBKDF2-SHA256."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        (salt + _SALT_PREFIX).encode("utf-8"),
        iterations=260_000,
    )
    return f"{salt}${dk.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    if "$" not in password_hash:
        return False
    salt, stored_hex = password_hash.split("$", 1)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        (salt + _SALT_PREFIX).encode("utf-8"),
        iterations=260_000,
    )
    return hmac.compare_digest(dk.hex(), stored_hex)


# ------------------------------------------------------------------ #
# JWT Token (lightweight — no pyjwt dependency)                        #
# ------------------------------------------------------------------ #

def _b64url_encode(data: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    import base64

    pad = 4 - len(s) % 4
    s += "=" * pad
    return base64.urlsafe_b64decode(s)


def _sign(data: str, secret: str) -> str:
    return _b64url_encode(
        hmac.new(
            secret.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    )


def create_access_token(
    user_id: int,
    company_id: int | None,
    site_id: int | None,
    role: str,
    expires_minutes: int = 480,
) -> str:
    """Create a simple HMAC-signed JWT-like access token."""
    settings = get_settings()
    header = _b64url_encode(b'{"alg":"HS256","typ":"MC"}')
    now = int(datetime.now(UTC).timestamp())
    payload_data = {
        "sub": str(user_id),
        "cid": company_id,
        "sid": site_id,
        "role": role,
        "iat": now,
        "exp": now + expires_minutes * 60,
    }
    import json

    payload = _b64url_encode(json.dumps(payload_data).encode("utf-8"))
    sig = _sign(f"{header}.{payload}", settings.missioncontrol_secret_key)
    return f"{header}.{payload}.{sig}"


def decode_access_token(token: str) -> dict:
    """Decode and verify an access token. Raises ValueError on failure."""
    settings = get_settings()
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header, payload, sig = parts
    expected_sig = _sign(f"{header}.{payload}", settings.missioncontrol_secret_key)
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Invalid token signature")

    import json

    data = json.loads(_b64url_decode(payload))
    now = int(datetime.now(UTC).timestamp())
    if data.get("exp", 0) < now:
        raise ValueError("Token expired")

    return data


# ------------------------------------------------------------------ #
# Auth Service                                                         #
# ------------------------------------------------------------------ #


class AuthService:
    """Authentication and user management service."""

    @staticmethod
    def authenticate(
        db: Session, email: str, password: str
    ) -> tuple[User, str]:
        """Authenticate a user and return (user, access_token)."""
        stmt = select(User).where(User.email == email.lower().strip())
        user = db.scalar(stmt)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        user.last_login = datetime.now(UTC)
        db.commit()

        token = create_access_token(
            user_id=user.id,
            company_id=user.company_id,
            site_id=user.site_id,
            role=user.role,
        )
        return user, token

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        display_name: str,
        password: str,
        role: str = "readonly",
        company_id: int | None = None,
        site_id: int | None = None,
    ) -> User:
        """Create a new user."""
        if role not in ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}",
            )

        existing = db.scalar(
            select(User).where(User.email == email.lower().strip())
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        user = User(
            email=email.lower().strip(),
            display_name=display_name,
            password_hash=hash_password(password),
            role=role,
            company_id=company_id,
            site_id=site_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Validate a token and return the user."""
        data = decode_access_token(token)
        user_id = int(data["sub"])
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if not user.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled",
            )
        return user
