"""
Mission Control Setup Service

Handles first-time installation detection and bootstrap.
Creates the initial Company, Site, and Global Administrator
in a single transaction. Automatically disables itself once
the first user exists.
"""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.company import Company
from app.models.db.site import Site
from app.models.db.user import User
from app.schemas.setup import BootstrapRequest
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


def is_setup_required(db: Session) -> bool:
    """Check whether any users exist in the database."""
    count = db.scalar(select(func.count()).select_from(User))
    return (count or 0) == 0


def bootstrap(db: Session, data: BootstrapRequest) -> dict:
    """
    Create Company, Site, and Global Administrator in one transaction.

    Raises HTTPException on validation failure. The entire creation
    is wrapped in a transaction that rolls back on any error.
    """
    # ── Validate ────────────────────────────────────────────────

    if data.admin_password != data.admin_confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    if len(data.admin_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    if db.scalar(
        select(User).where(User.email == data.admin_email.lower().strip())
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    if db.scalar(
        select(Company).where(Company.name == data.company_name.strip())
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A company with this name already exists",
        )

    if db.scalar(
        select(Site).where(Site.name == data.site_name.strip())
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A site with this name already exists",
        )

    if not is_setup_required(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup has already been completed",
        )

    # ── Create in transaction ───────────────────────────────────

    try:
        company = Company(
            uuid=str(uuid.uuid4()),
            name=data.company_name.strip(),
            display_name=data.company_name.strip(),
            status="active",
            enabled=True,
            is_global=False,
            timezone=data.site_timezone,
            max_sites=10,
            max_agents=100,
            max_users=50,
        )
        db.add(company)
        db.flush()

        site = Site(
            company_id=company.id,
            name=data.site_name.strip(),
            code=data.site_name.strip().lower().replace(" ", "-")[:100],
            description="Primary site",
            enabled=True,
            is_default=True,
            timezone=data.site_timezone,
        )
        db.add(site)
        db.flush()

        admin = User(
            email=data.admin_email.lower().strip(),
            display_name=data.admin_display_name.strip(),
            password_hash=hash_password(data.admin_password),
            role="global_admin",
            company_id=company.id,
            site_id=site.id,
            enabled=True,
        )
        db.add(admin)
        db.flush()

        logger.info(
            "Bootstrap complete: company=%d site=%d admin=%d",
            company.id,
            site.id,
            admin.id,
        )

        db.commit()

        return {
            "company_id": company.id,
            "site_id": site.id,
            "admin_id": admin.id,
            "message": "Installation complete. You can now log in.",
        }

    except Exception:
        db.rollback()
        logger.exception("Bootstrap failed — transaction rolled back")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bootstrap failed. Please try again.",
        ) from None
