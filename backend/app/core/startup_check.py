"""
Mission Control Startup Configuration Check

Comprehensive first-run validation that verifies every subsystem
required for Mission Control to operate. Provides human-friendly
error messages instead of raw tracebacks.
"""

import os
import platform
import sys

_BANNER = """
============================================================
  Mission Control Startup Error
============================================================

  {message}

  {instruction}

============================================================
"""


class CheckResult:
    """Result of a single startup check."""

    __slots__ = ("name", "ok", "message", "instruction", "critical")

    def __init__(
        self,
        name: str,
        ok: bool,
        message: str,
        instruction: str = "",
        critical: bool = False,
    ):
        self.name = name
        self.ok = ok
        self.message = message
        self.instruction = instruction
        self.critical = critical

    def __repr__(self) -> str:
        status = "PASS" if self.ok else ("CRIT" if self.critical else "WARN")
        return f"[{status}] {self.name}: {self.message}"


def _fail(message: str, instruction: str) -> None:
    """Print a friendly error and exit."""
    print(
        _BANNER.format(message=message, instruction=instruction),
        file=sys.stderr,
    )
    sys.exit(1)


def _banner_line(char: str = "─", width: int = 60) -> str:
    return char * width


def _print_check(result: CheckResult) -> None:
    icon = "✓" if result.ok else ("✗" if result.critical else "!")
    print(f"  {icon} {result.name}: {result.message}")


# ------------------------------------------------------------------ #
# Individual Checks                                                    #
# ------------------------------------------------------------------ #


def check_python_version() -> CheckResult:
    """Verify Python version is supported."""
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 12:
        return CheckResult(
            "Python Version",
            True,
            f"{major}.{minor}.{sys.version_info[2]}",
        )
    return CheckResult(
        "Python Version",
        False,
        f"{major}.{minor} is not supported. Requires Python 3.12+.",
        instruction=(
            "Install Python 3.12 or later:\n"
            "  Ubuntu: sudo apt install python3.12\n"
            "  Windows: https://www.python.org/downloads/\n"
            "  Docker: use the official python:3.12 image"
        ),
        critical=True,
    )


def check_required_env_vars() -> list[CheckResult]:
    """Verify all required environment variables are set."""
    results = []

    required = {
        "MISSIONCONTROL_SECRET_KEY": (
            "Generate one using:\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        ),
    }

    optional = {
        "POSTGRES_DB": "mission_control",
        "POSTGRES_USER": "missioncontrol",
        "POSTGRES_PASSWORD": "",
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": "5432",
        "REDIS_HOST": "redis",
        "REDIS_PORT": "6379",
        "ENVIRONMENT": "development",
        "EDITION": "community",
    }

    for var, instruction in required.items():
        value = os.environ.get(var, "").strip()
        if not value:
            results.append(
                CheckResult(
                    f"Env: {var}",
                    False,
                    "missing or empty",
                    instruction=instruction,
                    critical=True,
                )
            )
        else:
            results.append(
                CheckResult(f"Env: {var}", True, "set")
            )

    for var, default in optional.items():
        value = os.environ.get(var, "").strip()
        if not value:
            results.append(
                CheckResult(
                    f"Env: {var}",
                    True,
                    f"not set (using default: {default!r})",
                )
            )
        else:
            results.append(
                CheckResult(f"Env: {var}", True, "set")
            )

    return results


def check_secret_key_validity() -> CheckResult:
    """Validate the Fernet secret key format."""
    key = os.environ.get("MISSIONCONTROL_SECRET_KEY", "").strip()
    if not key:
        return CheckResult(
            "Secret Key",
            False,
            "not set",
            instruction="Set MISSIONCONTROL_SECRET_KEY in your .env file.",
            critical=True,
        )

    try:
        from cryptography.fernet import Fernet, InvalidToken

        Fernet(key.encode() if isinstance(key, str) else key)
    except (InvalidToken, ValueError):
        return CheckResult(
            "Secret Key",
            False,
            "invalid Fernet key format",
            instruction=(
                "Generate a new key:\n"
                '  python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            ),
            critical=True,
        )

    return CheckResult("Secret Key", True, "valid")


def check_postgres_connectivity() -> CheckResult:
    """Verify PostgreSQL is reachable."""
    try:
        import psycopg

        from app.core.config import get_settings

        settings = get_settings()
        dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
        conn = psycopg.connect(dsn)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        return CheckResult("PostgreSQL", True, "connected")
    except ImportError:
        return CheckResult(
            "PostgreSQL",
            False,
            "psycopg not installed",
            instruction="Install psycopg: pip install psycopg[binary]",
            critical=True,
        )
    except Exception as e:
        return CheckResult(
            "PostgreSQL",
            False,
            f"connection failed: {e}",
            instruction=(
                "Ensure PostgreSQL is running and accessible.\n"
                "Check POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD."
            ),
            critical=True,
        )


def check_redis_connectivity() -> CheckResult:
    """Verify Redis is reachable."""
    try:
        import redis

        from app.core.config import get_settings

        settings = get_settings()
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        r.close()
        return CheckResult("Redis", True, "connected")
    except ImportError:
        return CheckResult(
            "Redis",
            False,
            "redis-py not installed",
            instruction="Install redis: pip install redis",
            critical=True,
        )
    except Exception as e:
        return CheckResult(
            "Redis",
            False,
            f"connection failed: {e}",
            instruction=(
                "Ensure Redis is running and accessible.\n"
                "Check REDIS_HOST and REDIS_PORT."
            ),
            critical=True,
        )


def check_database_schema() -> CheckResult:
    """Verify database schema is up to date."""
    try:
        import psycopg

        from app.core.config import get_settings

        settings = get_settings()
        dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
        conn = psycopg.connect(dsn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'users')"
            )
            exists = cur.fetchone()[0]
        conn.close()

        if exists:
            return CheckResult("Database Schema", True, "tables present")
        return CheckResult(
            "Database Schema",
            False,
            "tables missing (fresh database?)",
            instruction="Run: alembic upgrade head",
            critical=True,
        )
    except Exception as e:
        return CheckResult(
            "Database Schema",
            False,
            f"check failed: {e}",
            instruction=(
                "Ensure the database is accessible and "
                "migrations have been applied."
            ),
            critical=True,
        )


def check_write_permissions() -> CheckResult:
    """Verify write permissions to key directories."""
    import tempfile

    dirs_to_check = [
        os.path.join(tempfile.gettempdir(), "missioncontrol"),
        os.path.join(os.path.expanduser("~"), ".config", "mission-control"),
    ]

    issues = []
    for d in dirs_to_check:
        try:
            os.makedirs(d, exist_ok=True)
            test_file = os.path.join(d, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except OSError as e:
            issues.append(f"{d}: {e}")

    if issues:
        return CheckResult(
            "Write Permissions",
            False,
            "; ".join(issues),
            instruction=(
                "Ensure the application has write access "
                "to temp and config directories."
            ),
            critical=False,
        )

    return CheckResult("Write Permissions", True, "writable")


def check_required_directories() -> CheckResult:
    """Verify required directories exist or can be created."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs = {
        "plugins": os.path.join(base, "plugins"),
        "logs": os.path.join(base, "logs"),
        "data": os.path.join(base, "data"),
    }

    issues = []
    for name, path in dirs.items():
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            issues.append(f"{name} ({path}): {e}")

    if issues:
        return CheckResult(
            "Required Directories",
            False,
            "; ".join(issues),
            instruction=(
                "Ensure the application can create directories "
                "in the project root."
            ),
            critical=True,
        )

    return CheckResult("Required Directories", True, "all present")


def check_platform() -> CheckResult:
    """Report the current platform."""
    system = platform.system()
    release = platform.release()
    return CheckResult(
        "Platform",
        True,
        f"{system} {release} ({platform.machine()})",
    )


def check_event_bus() -> CheckResult:
    """Verify the event bus module is importable."""
    try:
        from app.events import EventBus  # noqa: F401

        return CheckResult("Event Bus", True, "importable")
    except Exception as e:
        return CheckResult(
            "Event Bus",
            False,
            f"import failed: {e}",
            instruction="Check app/events/__init__.py for import errors.",
            critical=False,
        )


def check_heartbeat_service() -> CheckResult:
    """Verify the heartbeat service module is importable."""
    try:
        from app.heartbeat import HeartbeatService  # noqa: F401

        return CheckResult("Heartbeat Service", True, "importable")
    except Exception as e:
        return CheckResult(
            "Heartbeat Service",
            False,
            f"import failed: {e}",
            instruction="Check app/heartbeat/__init__.py for import errors.",
            critical=False,
        )


def check_agent_state_engine() -> CheckResult:
    """Verify the agent state engine module is importable."""
    try:
        from app.state import AgentStateEngine  # noqa: F401

        return CheckResult("Agent State Engine", True, "importable")
    except Exception as e:
        return CheckResult(
            "Agent State Engine",
            False,
            f"import failed: {e}",
            instruction="Check app/state/__init__.py for import errors.",
            critical=False,
        )


def check_plugin_loader() -> CheckResult:
    """Verify the plugin loader module is importable."""
    try:
        from app.plugins.loader import PluginLoader  # noqa: F401

        return CheckResult("Plugin Loader", True, "importable")
    except Exception as e:
        return CheckResult(
            "Plugin Loader",
            False,
            f"import failed: {e}",
            instruction="Check app/plugins/loader.py for import errors.",
            critical=False,
        )


def check_duplicate_plugins() -> CheckResult:
    """Check for duplicate plugin IDs in the plugins directory."""
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugins_dir = os.path.join(base, "plugins")
        if not os.path.isdir(plugins_dir):
            return CheckResult("Plugin Duplicates", True, "no plugins directory")

        ids: dict[str, str] = {}
        for entry in os.listdir(plugins_dir):
            manifest = os.path.join(plugins_dir, entry, "manifest.json")
            if os.path.isfile(manifest):
                import json

                with open(manifest) as f:
                    data = json.load(f)
                pid = data.get("id", entry)
                if pid in ids:
                    return CheckResult(
                        "Plugin Duplicates",
                        False,
                        f"plugin ID '{pid}' found in both {ids[pid]} and {entry}",
                        instruction="Remove or rename one of the duplicate plugins.",
                        critical=False,
                    )
                ids[pid] = entry

        count = len(ids)
        return CheckResult(
            "Plugin Duplicates", True, f"{count} plugins, no duplicates"
        )
    except Exception as e:
        return CheckResult(
            "Plugin Duplicates",
            False,
            f"check failed: {e}",
            critical=False,
        )


# ------------------------------------------------------------------ #
# Full Validation                                                       #
# ------------------------------------------------------------------ #


def run_all_checks() -> list[CheckResult]:
    """Run all startup checks and return results."""
    results = [
        check_platform(),
        check_python_version(),
    ]
    results.extend(check_required_env_vars())
    results.append(check_secret_key_validity())
    results.append(check_write_permissions())
    results.append(check_required_directories())
    results.append(check_postgres_connectivity())
    results.append(check_redis_connectivity())
    results.append(check_database_schema())
    results.append(check_event_bus())
    results.append(check_heartbeat_service())
    results.append(check_agent_state_engine())
    results.append(check_plugin_loader())
    results.append(check_duplicate_plugins())
    return results


def print_startup_report(results: list[CheckResult]) -> None:
    """Print a formatted startup report."""
    print("")
    print("  Mission Control — Startup Validation")
    print(f"  {_banner_line()}")
    print("")

    for r in results:
        _print_check(r)

    passed = sum(1 for r in results if r.ok)
    failed_critical = [r for r in results if not r.ok and r.critical]
    failed_warnings = [r for r in results if not r.ok and not r.critical]

    print("")
    print(f"  {passed}/{len(results)} checks passed")

    if failed_critical:
        print(f"  {len(failed_critical)} critical failure(s)")
        print("")
        for r in failed_critical:
            print(f"  FIX: {r.name}")
            if r.instruction:
                for line in r.instruction.split("\n"):
                    print(f"    {line}")
            print("")

    if failed_warnings:
        print(f"  {len(failed_warnings)} warning(s) — startup will continue")
        for r in failed_warnings:
            print(f"  WARN: {r.name}: {r.message}")

    print(f"  {_banner_line()}")
    print("")


def validate_startup(abort_on_critical: bool = True) -> bool:
    """
    Run all startup checks.

    Returns True if all checks pass.
    If abort_on_critical is True, exits on critical failures.
    """
    results = run_all_checks()
    print_startup_report(results)

    critical_failures = [r for r in results if not r.ok and r.critical]

    if critical_failures and abort_on_critical:
        first = critical_failures[0]
        _fail(
            message=f"{first.name}: {first.message}",
            instruction=first.instruction,
        )

    return len(critical_failures) == 0


# ------------------------------------------------------------------ #
# Legacy API (backwards compatibility)                                 #
# ------------------------------------------------------------------ #


def validate_secret_key() -> str:
    """Validate MISSIONCONTROL_SECRET_KEY. Returns key or exits."""
    result = check_secret_key_validity()
    if not result.ok:
        _fail(message=result.message, instruction=result.instruction)
    return os.environ.get("MISSIONCONTROL_SECRET_KEY", "").strip()


def validate_all() -> dict[str, str]:
    """Run all startup validations. Returns dict of validated values."""
    validate_startup(abort_on_critical=True)
    return {"secret_key": validate_secret_key()}
