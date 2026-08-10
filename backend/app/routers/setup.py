"""
Mission Control Setup Router

Endpoints for first-time installation and upgrade workflows.
Available only before initialization completes (no users exist).
After bootstrap, all setup endpoints return 403.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.db.company import Company
from app.models.db.user import User
from app.schemas.setup import (
    BootstrapRequest,
    BootstrapResponse,
    SetupStatusResponse,
)
from app.services.setup_service import bootstrap, is_setup_required

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setup", tags=["Setup"])


# ------------------------------------------------------------------ #
# Helper: enforce pre-bootstrap state                                  #
# ------------------------------------------------------------------ #


def _require_setup(db: Session) -> None:
    """Raise 403 if setup has already been completed."""
    if not is_setup_required(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup has already been completed",
        )


# ------------------------------------------------------------------ #
# Request / Response schemas                                           #
# ------------------------------------------------------------------ #


class ValidateRequest(BaseModel):
    """Parameters to validate before bootstrap."""

    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="mission_control")
    postgres_password: str = Field(default="")
    postgres_db: str = Field(default="mission_control")
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    secret_key: str = Field(default="")


class ValidateResult(BaseModel):
    """Result of a single validation check."""

    ok: bool
    message: str


class ValidateResponse(BaseModel):
    """Aggregate validation results."""

    postgres: ValidateResult
    redis: ValidateResult
    secret_key: ValidateResult
    all_ok: bool


class CreateAdminRequest(BaseModel):
    """Create an administrator account (separate from full bootstrap)."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    site_name: str = Field(..., min_length=1, max_length=200)
    timezone: str = Field(default="UTC", max_length=100)


class EntityResult(BaseModel):
    """Status of a created or skipped entity."""

    created: bool
    id: int | None = None
    skipped: bool = False


class CreateAdminResponse(BaseModel):
    """Result of administrator creation."""

    company: EntityResult
    site: EntityResult
    admin: EntityResult
    message: str


class CompleteResponse(BaseModel):
    """Result of marking setup as complete."""

    setup_required: bool
    user_count: int
    company_count: int
    message: str


class ReadinessResponse(BaseModel):
    """Production readiness assessment."""

    score: int
    production_ready: bool
    dimensions: dict
    issues: list[str]
    recommendations: list[str]


class UpgradeCheckResponse(BaseModel):
    """Upgrade readiness assessment."""

    overall_status: str
    checks: dict
    upgrade_plan: dict


# ------------------------------------------------------------------ #
# Endpoints                                                             #
# ------------------------------------------------------------------ #


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(
    db: Session = Depends(get_db),
) -> SetupStatusResponse:
    """Check whether the setup wizard is required."""
    tz = "UTC"
    try:
        from app.services.company_service import CompanyService
        service = CompanyService()
        companies = service.get_all(db)
        if companies and companies[0].timezone:
            tz = companies[0].timezone
    except Exception as exc:
        logger.debug("Could not load timezone for setup status: %s", exc)
    return SetupStatusResponse(setup_required=is_setup_required(db), timezone=tz)


@router.post(
    "/bootstrap",
    response_model=BootstrapResponse,
    status_code=201,
)
async def run_bootstrap(
    payload: BootstrapRequest,
    db: Session = Depends(get_db),
) -> BootstrapResponse:
    """
    Create the first Company, Site, and Global Administrator.

    Only works when no users exist. After completion, the setup
    wizard is permanently disabled.
    """
    result = bootstrap(db, payload)
    return BootstrapResponse(**result)


@router.post(
    "/validate",
    response_model=ValidateResponse,
    status_code=200,
)
async def validate_setup(
    payload: ValidateRequest,
    db: Session = Depends(get_db),
) -> ValidateResponse:
    """
    Validate setup parameters before bootstrap.

    Tests PostgreSQL connectivity, Redis connectivity, and
    the Fernet secret key format.
    """
    _require_setup(db)

    # ── PostgreSQL ───────────────────────────────────────────────
    pg_result = ValidateResult(ok=False, message="")
    try:
        import psycopg

        try:
            conn = psycopg.connect(
                host=payload.postgres_host,
                port=payload.postgres_port,
                user=payload.postgres_user,
                password=payload.postgres_password,
                dbname=payload.postgres_db,
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
            conn.close()
            pg_result = ValidateResult(ok=True, message=f"Connected: {version}")
        except Exception as exc:
            pg_result = ValidateResult(ok=False, message=f"Connection failed: {exc}")
    except ImportError:
        pg_result = ValidateResult(ok=False, message="psycopg package not installed")

    # ── Redis ────────────────────────────────────────────────────
    redis_result = ValidateResult(ok=False, message="")
    try:
        import redis

        try:
            client = redis.Redis(
                host=payload.redis_host,
                port=payload.redis_port,
                socket_connect_timeout=5,
            )
            info = client.info("server")
            version = info.get("redis_version", "unknown")
            client.close()
            redis_result = ValidateResult(ok=True, message=f"Connected: Redis {version}")
        except Exception as exc:
            redis_result = ValidateResult(ok=False, message=f"Connection failed: {exc}")
    except ImportError:
        redis_result = ValidateResult(ok=False, message="redis package not installed")

    # ── Secret key ──────────────────────────────────────────────
    sk_result = ValidateResult(ok=False, message="")
    key = payload.secret_key
    if not key:
        sk_result = ValidateResult(ok=False, message="Secret key is empty")
    else:
        try:
            from cryptography.fernet import Fernet, InvalidToken

            try:
                Fernet(key.encode() if isinstance(key, str) else key)
                sk_result = ValidateResult(ok=True, message="Valid Fernet key")
            except (InvalidToken, ValueError):
                sk_result = ValidateResult(
                    ok=False,
                    message=(
                        "Invalid Fernet key. Generate with: "
                        'python -c "from cryptography.fernet import Fernet; '
                        'print(Fernet.generate_key().decode())"'
                    ),
                )
        except ImportError:
            sk_result = ValidateResult(ok=False, message="cryptography package not installed")

    all_ok = pg_result.ok and redis_result.ok and sk_result.ok

    return ValidateResponse(
        postgres=pg_result,
        redis=redis_result,
        secret_key=sk_result,
        all_ok=all_ok,
    )


@router.post(
    "/create-admin",
    response_model=CreateAdminResponse,
    status_code=201,
)
async def create_admin(
    payload: CreateAdminRequest,
    db: Session = Depends(get_db),
) -> CreateAdminResponse:
    """
    Create an administrator account separately from full bootstrap.

    Creates company, site, and admin user in an idempotent fashion.
    Existing entities are skipped.
    """
    _require_setup(db)

    try:
        from app.setup.wizard import SetupWizard

        wizard = SetupWizard(db)
        result = wizard.create_administrator(
            db=db,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            company_name=payload.company_name,
            site_name=payload.site_name,
            timezone=payload.timezone,
        )

        company_result = EntityResult(**result["company"])
        site_result = EntityResult(**result["site"])
        admin_result = EntityResult(**result["admin"])

        created_count = sum(
            1 for e in (company_result, site_result, admin_result) if e.created
        )
        skipped_count = sum(
            1 for e in (company_result, site_result, admin_result) if e.skipped
        )

        message_parts: list[str] = []
        if created_count:
            message_parts.append(f"Created {created_count} entity(ies)")
        if skipped_count:
            message_parts.append(f"Skipped {skipped_count} existing")

        return CreateAdminResponse(
            company=company_result,
            site=site_result,
            admin=admin_result,
            message=". ".join(message_parts) if message_parts else "No changes",
        )

    except Exception as exc:
        logger.exception("create_admin failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Administrator creation failed: {exc}",
        ) from exc


@router.post(
    "/complete",
    response_model=CompleteResponse,
    status_code=200,
)
async def complete_setup(
    db: Session = Depends(get_db),
) -> CompleteResponse:
    """
    Mark setup as complete and return current state.

    Verifies that at least one user exists, confirming that
    bootstrap has been performed.
    """
    if is_setup_required(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup is not yet complete — no users exist",
        )

    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    company_count = db.scalar(
        select(func.count()).select_from(Company)
    ) or 0

    return CompleteResponse(
        setup_required=False,
        user_count=user_count,
        company_count=company_count,
        message="Setup is complete. The system is ready for use.",
    )


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    status_code=200,
)
async def get_readiness(
    db: Session = Depends(get_db),
) -> ReadinessResponse:
    """
    Get production readiness score.

    Runs ReadinessChecker.assess_all() and returns a weighted
    score across all dimensions.
    """
    try:
        from app.setup.readiness import ReadinessChecker

        checker = ReadinessChecker(db=db)
        score, details = checker.get_score()

        return ReadinessResponse(
            score=score,
            production_ready=details["production_ready"],
            dimensions=details["dimensions"],
            issues=details["issues"],
            recommendations=details["recommendations"],
        )
    except Exception as exc:
        logger.exception("readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Readiness check failed: {exc}",
        ) from exc


@router.get(
    "/upgrade-check",
    response_model=UpgradeCheckResponse,
    status_code=200,
)
async def upgrade_check(
    db: Session = Depends(get_db),
) -> UpgradeCheckResponse:
    """
    Check upgrade readiness.

    Runs UpgradeAssistant.check_all() and generate_upgrade_plan()
    to determine what steps are needed for an upgrade.
    """
    try:
        from app.setup.upgrade_assistant import UpgradeAssistant

        assistant = UpgradeAssistant(db=db)
        checks = assistant.check_all()
        plan = assistant.generate_upgrade_plan()

        return UpgradeCheckResponse(
            overall_status=checks["overall_status"],
            checks=checks["checks"],
            upgrade_plan=plan,
        )
    except Exception as exc:
        logger.exception("upgrade check failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upgrade check failed: {exc}",
        ) from exc
