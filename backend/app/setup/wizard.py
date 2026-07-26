"""
Mission Control Interactive Setup Wizard

Guided setup for first-time installations.
Detects fresh/existing/upgrade installations and collects configuration.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db.company import Company
from app.models.db.site import Site
from app.models.db.user import User
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


class SetupWizard:
    """Interactive setup wizard for Mission Control installations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ #
    # Installation detection                                               #
    # ------------------------------------------------------------------ #

    def detect_installation_type(self) -> str:
        """Detect the current installation state.

        Returns one of:
            "fresh"      — no users exist yet
            "upgrade"    — users exist but schema appears outdated
            "existing"   — users exist, installation looks current
            "reconfigure" — existing installation that needs reconfiguration
        """
        user_count = self.db.scalar(select(func.count()).select_from(User)) or 0

        if user_count == 0:
            return "fresh"

        if self._has_outdated_schema():
            return "upgrade"

        return "existing"

    def _has_outdated_schema(self) -> bool:
        """Heuristic check for outdated schema.

        Checks for columns/tables that were added in recent migrations.
        Returns True if the database appears to pre-date the current version.
        """
        try:
            from sqlalchemy import inspect as sa_inspect

            inspector = sa_inspect(self.db.get_bind())
            tables = inspector.get_table_names()

            if "users" not in tables:
                return True

            user_columns = {
                col["name"]
                for col in inspector.get_columns("users")
            }

            if "role" not in user_columns:
                return True

            return False
        except Exception:
            logger.debug("Schema version check failed, assuming current")
            return False

    # ------------------------------------------------------------------ #
    # Edition selection                                                    #
    # ------------------------------------------------------------------ #

    def collect_edition(self) -> str:
        """Return the edition to install.

        For CLI use this returns the default "community" edition.
        Interactive prompts would be handled by the calling layer.
        """
        return "community"

    # ------------------------------------------------------------------ #
    # Validation helpers                                                   #
    # ------------------------------------------------------------------ #

    def validate_postgres(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        dbname: str,
    ) -> dict:
        """Test a PostgreSQL connection.

        Returns {"ok": bool, "message": str}.
        """
        try:
            import psycopg

            conn = psycopg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
            conn.close()
            return {"ok": True, "message": f"Connected: {version}"}
        except ImportError:
            return {
                "ok": False,
                "message": "psycopg package not installed",
            }
        except Exception as exc:
            return {"ok": False, "message": f"Connection failed: {exc}"}

    def validate_redis(self, host: str, port: int) -> dict:
        """Test a Redis connection.

        Returns {"ok": bool, "message": str}.
        """
        try:
            import redis

            client = redis.Redis(
                host=host,
                port=port,
                socket_connect_timeout=5,
            )
            info = client.info("server")
            version = info.get("redis_version", "unknown")
            client.close()
            return {"ok": True, "message": f"Connected: Redis {version}"}
        except ImportError:
            return {
                "ok": False,
                "message": "redis package not installed",
            }
        except Exception as exc:
            return {"ok": False, "message": f"Connection failed: {exc}"}

    def validate_secret_key(self, key: str) -> dict:
        """Validate a Fernet key format.

        Returns {"ok": bool, "message": str}.
        """
        if not key:
            return {"ok": False, "message": "Secret key is empty"}

        try:
            from cryptography.fernet import Fernet, InvalidToken

            try:
                Fernet(key.encode() if isinstance(key, str) else key)
            except (InvalidToken, ValueError):
                return {
                    "ok": False,
                    "message": (
                        "Invalid Fernet key format. Generate one with: "
                        'python -c "from cryptography.fernet import Fernet; '
                        'print(Fernet.generate_key().decode())"'
                    ),
                }
            return {"ok": True, "message": "Valid Fernet key"}
        except ImportError:
            return {
                "ok": False,
                "message": "cryptography package not installed",
            }

    # ------------------------------------------------------------------ #
    # Administrator creation (idempotent)                                 #
    # ------------------------------------------------------------------ #

    def create_administrator(
        self,
        db: Session,
        email: str,
        password: str,
        display_name: str,
        company_name: str,
        site_name: str,
        timezone: str = "UTC",
    ) -> dict:
        """Create admin user, company, and site in an idempotent fashion.

        Existing entities are skipped. Returns a dict describing what was
        created versus what already existed.
        """
        result: dict = {
            "company": {"created": False, "id": None, "skipped": False},
            "site": {"created": False, "id": None, "skipped": False},
            "admin": {"created": False, "id": None, "skipped": False},
        }

        # ── Company ──────────────────────────────────────────────
        company = db.scalar(
            select(Company).where(Company.name == company_name.strip())
        )
        if company is not None:
            result["company"]["skipped"] = True
            result["company"]["id"] = company.id
        else:
            company = Company(
                uuid=str(uuid.uuid4()),
                name=company_name.strip(),
                display_name=company_name.strip(),
                status="active",
                enabled=True,
                is_global=False,
                timezone=timezone,
                max_sites=10,
                max_agents=100,
                max_users=50,
            )
            db.add(company)
            db.flush()
            result["company"]["created"] = True
            result["company"]["id"] = company.id

        # ── Site ─────────────────────────────────────────────────
        site = db.scalar(
            select(Site).where(Site.name == site_name.strip())
        )
        if site is not None:
            result["site"]["skipped"] = True
            result["site"]["id"] = site.id
        else:
            site = Site(
                company_id=company.id,
                name=site_name.strip(),
                code=site_name.strip().lower().replace(" ", "-")[:100],
                description="Primary site",
                enabled=True,
                is_default=True,
                timezone=timezone,
            )
            db.add(site)
            db.flush()
            result["site"]["created"] = True
            result["site"]["id"] = site.id

        # ── Admin user ───────────────────────────────────────────
        existing_user = db.scalar(
            select(User).where(User.email == email.lower().strip())
        )
        if existing_user is not None:
            result["admin"]["skipped"] = True
            result["admin"]["id"] = existing_user.id
        else:
            admin = User(
                email=email.lower().strip(),
                display_name=display_name.strip(),
                password_hash=hash_password(password),
                role="global_admin",
                company_id=company.id,
                site_id=site.id,
                enabled=True,
            )
            db.add(admin)
            db.flush()
            result["admin"]["created"] = True
            result["admin"]["id"] = admin.id

        db.commit()

        logger.info(
            "create_administrator result: company=%s site=%s admin=%s",
            result["company"],
            result["site"],
            result["admin"],
        )
        return result

    # ------------------------------------------------------------------ #
    # Status                                                               #
    # ------------------------------------------------------------------ #

    def get_status(self, db: Session) -> dict:
        """Return a summary of the current setup state."""
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        company_count = db.scalar(
            select(func.count()).select_from(Company)
        ) or 0
        site_count = db.scalar(select(func.count()).select_from(Site)) or 0
        installation_type = self.detect_installation_type()

        return {
            "installation_type": installation_type,
            "user_count": user_count,
            "company_count": company_count,
            "site_count": site_count,
            "setup_required": user_count == 0,
        }

    # ------------------------------------------------------------------ #
    # Full setup orchestration                                             #
    # ------------------------------------------------------------------ #

    def run_full_setup(self, db: Session, config: dict) -> dict:
        """Run the full setup sequence: validate → create admin → report.

        Expected *config* keys:
            admin_email, admin_password, admin_display_name,
            company_name, site_name, timezone (optional),
            postgres_host, postgres_port, postgres_user,
            postgres_password, postgres_dbname,
            redis_host, redis_port,
            secret_key
        """
        errors: list[str] = []

        # ── Validate Postgres ────────────────────────────────────
        pg = self.validate_postgres(
            host=config.get("postgres_host", "postgres"),
            port=config.get("postgres_port", 5432),
            user=config.get("postgres_user", ""),
            password=config.get("postgres_password", ""),
            dbname=config.get("postgres_dbname", "mission_control"),
        )
        if not pg["ok"]:
            errors.append(f"PostgreSQL: {pg['message']}")

        # ── Validate Redis ───────────────────────────────────────
        rd = self.validate_redis(
            host=config.get("redis_host", "redis"),
            port=config.get("redis_port", 6379),
        )
        if not rd["ok"]:
            errors.append(f"Redis: {rd['message']}")

        # ── Validate secret key ──────────────────────────────────
        sk = self.validate_secret_key(config.get("secret_key", ""))
        if not sk["ok"]:
            errors.append(f"Secret key: {sk['message']}")

        if errors:
            return {"ok": False, "errors": errors, "admin": None}

        # ── Create administrator ─────────────────────────────────
        admin_result = self.create_administrator(
            db=db,
            email=config["admin_email"],
            password=config["admin_password"],
            display_name=config.get("admin_display_name", "Administrator"),
            company_name=config["company_name"],
            site_name=config["site_name"],
            timezone=config.get("timezone", "UTC"),
        )

        return {"ok": True, "errors": [], "admin": admin_result}
