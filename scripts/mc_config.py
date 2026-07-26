"""
Mission Control CLI Configuration Utility

Standalone configuration management tool for Mission Control installations.

Usage:
    python scripts/mc_config.py <command> [options]

Commands:
    validate       Validate current configuration
    show           Display current configuration (secrets masked)
    edit           Open .env in editor (or print instructions)
    export <file>  Export configuration to a file
    import <file>  Import configuration from a file
    doctor         Run full system diagnostics
    reset          Reset configuration to defaults
    profile <name> Show or apply a deployment profile
    setup          Run interactive setup wizard
    version        Show version information
"""

import argparse
import os
import sys
from pathlib import Path

# ------------------------------------------------------------------ #
# ANSI helpers (no external dependencies)                              #
# ------------------------------------------------------------------ #

_B = "\033[1m"
_R = "\033[0m"
_G = "\033[32m"
_Y = "\033[33m"
_Rd = "\033[31m"
_C = "\033[36m"
_DIM = "\033[2m"


def _ok(msg: str) -> str:
    return f"{_G}{_B}OK{_R} {_G}{msg}{_R}"


def _warn(msg: str) -> str:
    return f"{_Y}{_B}WARN{_R} {_Y}{msg}{_R}"


def _fail(msg: str) -> str:
    return f"{_Rd}{_B}FAIL{_R} {_Rd}{msg}{_R}"


def _info(msg: str) -> str:
    return f"{_C}{msg}{_R}"


def _dim(msg: str) -> str:
    return f"{_DIM}{msg}{_R}"


def _heading(title: str) -> str:
    line = "-" * 50
    return f"\n{_B}{title}{_R}\n{line}"


# ------------------------------------------------------------------ #
# .env file helpers                                                    #
# ------------------------------------------------------------------ #

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
_ENV_EXAMPLE = _PROJECT_ROOT / ".env.example"

# Keys whose values should never be displayed in plain text.
_SECRET_KEYS = {
    "missioncontrol_secret_key",
    "secret_key",
    "postgres_password",
    "redis_password",
    "ad_password",
    "m365_client_secret",
    "zabbix_password",
}

_DEFAULT_ENV = """\
PROJECT_NAME=Mission Control
ENVIRONMENT=development
EDITION=community
MISSIONCONTROL_SECRET_KEY=CHANGE_ME
POSTGRES_DB=mission_control
POSTGRES_USER=mission_control
POSTGRES_PASSWORD=mission_control
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
BACKEND_CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:5173
COMPOSE_PROJECT_NAME=missioncontrol
"""


def _read_env(path: Path | None = None) -> dict[str, str]:
    """Parse a .env file into a flat dict (no interpolation)."""
    target = path or _ENV_PATH
    result: dict[str, str] = {}
    if not target.exists():
        return result
    with open(target, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip().strip("\"'")
            result[key] = value
    return result


def _write_env(data: dict[str, str], path: Path | None = None) -> None:
    """Write a dict as a .env file."""
    target = path or _ENV_PATH
    lines: list[str] = []
    for key, value in data.items():
        if value and (" " in value or "'" in value):
            lines.append(f'{key}="{value}"')
        else:
            lines.append(f"{key}={value}")
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _mask_value(key: str, value: str) -> str:
    """Mask secret values, showing only the first 4 characters."""
    if not value:
        return ""
    lower_key = key.lower()
    is_secret = any(s in lower_key for s in _SECRET_KEYS)
    if is_secret and len(value) > 4:
        return value[:4] + "***"
    if is_secret:
        return "***"
    return value


# ------------------------------------------------------------------ #
# sys.path setup for backend imports                                   #
# ------------------------------------------------------------------ #

def _setup_path() -> None:
    """Add backend/ to sys.path so app modules are importable."""
    backend_dir = _PROJECT_ROOT / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


# ------------------------------------------------------------------ #
# Commands                                                             #
# ------------------------------------------------------------------ #

def cmd_version(_args: argparse.Namespace) -> int:
    """Show version information."""
    version_file = _PROJECT_ROOT / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown"

    print(_heading("Mission Control - Version"))
    print(f"  Version:       {_B}{version}{_R}")
    print(f"  Project root:  {_dim(str(_PROJECT_ROOT))}")
    print(f"  Python:        {sys.version.split()[0]}")
    print(f"  Platform:      {sys.platform}")
    print(f"  Config file:   {_dim(str(_ENV_PATH))}")

    env = _read_env()
    if env:
        print(f"  Environment:   {env.get('ENVIRONMENT', 'unset')}")
        print(f"  Edition:       {env.get('EDITION', 'unset')}")
    else:
        print(f"  Config:        {_warn('no .env found')}")
    return 0


def cmd_show(_args: argparse.Namespace) -> int:
    """Display current configuration with secrets masked."""
    print(_heading("Mission Control - Configuration"))

    if not _ENV_PATH.exists():
        print(f"  {_warn('No .env file found at project root')}")
        print(f"  {_dim('Run `mc_config.py setup` to create one.')}")
        return 1

    env = _read_env()
    if not env:
        print(f"  {_warn('.env file is empty or unreadable')}")
        return 1

    max_key = max(len(k) for k in env)
    for key, value in env.items():
        masked = _mask_value(key, value)
        print(f"  {_C}{key:<{max_key}}{_R} = {masked}")

    print(f"\n  {_dim(f'{len(env)} settings loaded from {_ENV_PATH.name}')}")
    return 0


def cmd_validate(_args: argparse.Namespace) -> int:
    """Validate current configuration - connectivity, secrets, dirs."""
    print(_heading("Mission Control - Validate Configuration"))
    errors: list[str] = []
    warnings: list[str] = []

    # ── .env file ────────────────────────────────────────────────
    if not _ENV_PATH.exists():
        print(f"  {_fail('.env file not found')} at {_dim(str(_ENV_PATH))}")
        return 1

    env = _read_env()
    print(f"  {_ok('.env loaded')} - {len(env)} settings")

    # ── Secret key ──────────────────────────────────────────────
    secret = env.get("missioncontrol_secret_key", "")
    if not secret or secret == "CHANGE_ME":
        print(f"  {_fail('MISSIONCONTROL_SECRET_KEY is not set or still default')}")
        errors.append("secret_key")
    else:
        try:
            _setup_path()
            from cryptography.fernet import Fernet, InvalidToken

            try:
                Fernet(secret.encode() if isinstance(secret, str) else secret)
                print(f"  {_ok('SECRET_KEY is valid Fernet key')}")
            except (InvalidToken, ValueError):
                print(f"  {_fail('SECRET_KEY is not a valid Fernet key')}")
                errors.append("secret_key_format")
        except ImportError:
            print(f"  {_warn('cryptography package not installed - cannot validate key')}")

    # ── PostgreSQL ───────────────────────────────────────────────
    pg_host = env.get("postgres_host", "")
    pg_port = env.get("postgres_port", "5432")
    pg_user = env.get("postgres_user", "")
    pg_db = env.get("postgres_db", "")
    pg_pass = env.get("postgres_password", "")

    if not all([pg_host, pg_user, pg_db]):
        print(f"  {_fail('PostgreSQL config incomplete')} (host/user/db required)")
        errors.append("postgres_config")
    else:
        try:
            _setup_path()
            import psycopg

            try:
                conn = psycopg.connect(
                    host=pg_host,
                    port=int(pg_port),
                    user=pg_user,
                    password=pg_pass,
                    dbname=pg_db,
                    connect_timeout=5,
                )
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                conn.close()
                print(f"  {_ok('PostgreSQL connected')} - {version}")
            except Exception as exc:
                print(f"  {_fail(f'PostgreSQL connection failed: {exc}')}")
                errors.append("postgres_connection")
        except ImportError:
            print(f"  {_warn('psycopg package not installed - skipping PostgreSQL check')}")

    # ── Redis ────────────────────────────────────────────────────
    redis_host = env.get("redis_host", "")
    redis_port = env.get("redis_port", "6379")

    if not redis_host:
        print(f"  {_fail('Redis host not configured')}")
        errors.append("redis_config")
    else:
        try:
            _setup_path()
            import redis

            try:
                client = redis.Redis(
                    host=redis_host,
                    port=int(redis_port),
                    socket_connect_timeout=5,
                )
                info = client.info("server")
                version = info.get("redis_version", "unknown")
                client.close()
                print(f"  {_ok('Redis connected')} - v{version}")
            except Exception as exc:
                print(f"  {_fail(f'Redis connection failed: {exc}')}")
                errors.append("redis_connection")
        except ImportError:
            print(f"  {_warn('redis package not installed - skipping Redis check')}")

    # ── Required directories ─────────────────────────────────────
    dirs_to_check = [
        (_PROJECT_ROOT / "backend", "Backend"),
        (_PROJECT_ROOT / "frontend", "Frontend"),
        (_PROJECT_ROOT / "logs", "Logs"),
    ]
    for dir_path, label in dirs_to_check:
        if dir_path.exists():
            print(f"  {_ok(f'{label} directory exists')} - {_dim(str(dir_path))}")
        else:
            print(f"  {_warn(f'{label} directory missing')} - {_dim(str(dir_path))}")
            warnings.append(f"dir_{label.lower()}")

    # ── Summary ──────────────────────────────────────────────────
    print(_heading("Validation Summary"))
    if errors:
        print(f"  {_fail(f'{len(errors)} error(s) found')}")
        for e in errors:
            print(f"    - {e}")
    if warnings:
        print(f"  {_warn(f'{len(warnings)} warning(s)')}")
        for w in warnings:
            print(f"    - {w}")
    if not errors and not warnings:
        print(f"  {_ok('All checks passed')}")
    return 1 if errors else 0


def cmd_edit(_args: argparse.Namespace) -> int:
    """Open .env in the system editor or print instructions."""
    print(_heading("Mission Control - Edit Configuration"))

    if not _ENV_PATH.exists():
        print(f"  {_warn('.env not found - creating from defaults')}")
        _write_env(
            {k: v for k, v in (line.split("=", 1) for line in _DEFAULT_ENV.strip().splitlines() if "=" in line)}
        )
        print(f"  {_ok('Created .env with defaults')}")

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        print(f"  Opening {_dim(str(_ENV_PATH))} in {editor}...")
        os.execlp(editor, editor, str(_ENV_PATH))
    else:
        print(f"  {_dim('No $EDITOR set. Open this file manually:')}")
        print(f"  {_C}{_ENV_PATH}{_R}")
        print()
        print("  Set $EDITOR to open files automatically:")
        print("    export EDITOR=code      # VS Code")
        print("    export EDITOR=nano      # Nano")
        print("    export EDITOR=vim       # Vim")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export current .env to a file."""
    dest = Path(args.file)
    print(_heading("Mission Control - Export Configuration"))
    print(f"  {_dim(f'Exporting to {dest}')}")

    if not _ENV_PATH.exists():
        print(f"  {_fail('No .env file to export')}")
        return 1

    env = _read_env()
    _write_env(env, dest)
    print(f"  {_ok(f'Exported {len(env)} settings to {dest}')}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import configuration from a file into .env."""
    source = Path(args.file)
    print(_heading("Mission Control - Import Configuration"))
    print(f"  {_dim(f'Importing from {source}')}")

    if not source.exists():
        print(f"  {_fail(f'File not found: {source}')}")
        return 1

    imported = _read_env(source)
    if not imported:
        print(f"  {_fail('Source file contains no valid settings')}")
        return 1

    # Preserve existing if present
    existing = _read_env()
    merged = {**existing, **imported}
    _write_env(merged)

    new_keys = set(imported.keys()) - set(existing.keys())
    updated_keys = set(imported.keys()) & set(existing.keys())

    print(f"  {_ok(f'Imported {len(imported)} settings')}")
    if new_keys:
        print(f"    New:     {', '.join(sorted(new_keys))}")
    if updated_keys:
        print(f"    Updated: {', '.join(sorted(updated_keys))}")
    print(f"  {_dim(f'Written to {_ENV_PATH}')}")
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    """Run full system diagnostics and readiness check."""
    print(_heading("Mission Control - Doctor"))
    print(_dim("Running comprehensive diagnostics...\n"))

    _setup_path()
    results: list[tuple[str, bool, str]] = []

    # ── Python version ───────────────────────────────────────────
    py_ok = sys.version_info >= (3, 12)
    py_msg = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if py_ok:
        py_msg += " (3.12+ required)"
    results.append(("Python", py_ok, py_msg))

    # ── .env file ────────────────────────────────────────────────
    env_exists = _ENV_PATH.exists()
    results.append((".env file", env_exists, str(_ENV_PATH) if env_exists else "Missing"))

    # ── Packages ─────────────────────────────────────────────────
    required_pkgs = ["fastapi", "sqlalchemy", "pydantic", "psycopg", "redis", "cryptography"]
    for pkg in required_pkgs:
        try:
            __import__(pkg)
            results.append((f"Package: {pkg}", True, "installed"))
        except ImportError:
            results.append((f"Package: {pkg}", False, "NOT INSTALLED"))

    # ── PostgreSQL ───────────────────────────────────────────────
    env = _read_env()
    if env:
        pg_ok = False
        pg_msg = ""
        try:
            import psycopg

            conn = psycopg.connect(
                host=env.get("postgres_host", "localhost"),
                port=int(env.get("postgres_port", "5432")),
                user=env.get("postgres_user", ""),
                password=env.get("postgres_password", ""),
                dbname=env.get("postgres_db", "mission_control"),
                connect_timeout=5,
            )
            conn.close()
            pg_ok = True
            pg_msg = "Connection successful"
        except ImportError:
            pg_msg = "psycopg not installed"
        except Exception as exc:
            pg_msg = str(exc)[:80]
        results.append(("PostgreSQL", pg_ok, pg_msg))
    else:
        results.append(("PostgreSQL", False, "No .env - cannot check"))

    # ── Redis ────────────────────────────────────────────────────
    if env:
        redis_ok = False
        redis_msg = ""
        try:
            import redis as redis_lib

            client = redis_lib.Redis(
                host=env.get("redis_host", "localhost"),
                port=int(env.get("redis_port", "6379")),
                socket_connect_timeout=5,
            )
            client.ping()
            redis_ok = True
            redis_msg = "Connection successful"
        except ImportError:
            redis_msg = "redis package not installed"
        except Exception as exc:
            redis_msg = str(exc)[:80]
        results.append(("Redis", redis_ok, redis_msg))
    else:
        results.append(("Redis", False, "No .env - cannot check"))

    # ── Required directories ─────────────────────────────────────
    for name in ("backend", "frontend", "logs", "deployment"):
        d = _PROJECT_ROOT / name
        results.append((f"Dir: {name}", d.exists(), str(d)))

    # ── Readiness checker ────────────────────────────────────────
    try:
        from app.setup.readiness import ReadinessChecker

        checker = ReadinessChecker()
        score, details = checker.get_score()
        ready = details.get("production_ready", False)
        results.append((
            "Production readiness",
            ready,
            f"Score: {score}/100 {'(ready)' if ready else '(not ready)'}",
        ))

        # Show dimension breakdown
        for dim, dim_result in details.get("dimensions", {}).items():
            dim_score = dim_result.get("score", 0)
            dim_status = dim_result.get("status", "?")
            icon = dim_status == "PASS"
            results.append((f"  {dim}", icon, f"{dim_score}% - {dim_status}"))
    except Exception as exc:
        results.append(("Production readiness", False, f"Checker failed: {exc}"))

    # ── Print results ────────────────────────────────────────────
    for label, passed, detail in results:
        icon = _ok("") if passed else _fail("")
        padding = 28 - len(label)
        if padding < 1:
            padding = 1
        print(f"  {icon} {label}{' ' * padding}{_dim(detail)}")

    passed_count = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    print(f"\n  {_dim(f'{passed_count}/{total} checks passed')}")
    return 0 if passed_count == total else 1


def cmd_reset(_args: argparse.Namespace) -> int:
    """Reset configuration to defaults (with confirmation)."""
    print(_heading("Mission Control - Reset Configuration"))

    if _ENV_PATH.exists():
        backup = _ENV_PATH.with_suffix(".env.bak")
        import shutil

        shutil.copy2(_ENV_PATH, backup)
        print(f"  {_dim(f'Current .env backed up to {backup.name}')}")

    if not _args.yes:
        answer = input("  Are you sure you want to reset? This will overwrite your .env [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("  Cancelled.")
            return 0

    env_data = {}
    for line in _DEFAULT_ENV.strip().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            env_data[key.strip()] = value.strip()
    _write_env(env_data)

    print(f"  {_ok('Configuration reset to defaults')}")
    print(f"  {_dim('Remember to set MISSIONCONTROL_SECRET_KEY before starting.')}")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    """Show or apply a deployment profile."""
    print(_heading("Mission Control - Deployment Profile"))

    name = args.profile_name

    # Import profile system
    _setup_path()
    try:
        from app.setup.profiles import DeploymentProfile
    except ImportError:
        print(f"  {_warn('DeploymentProfile not available - listing built-in profiles instead')}")
        print()
        profiles = {
            "development": "Local development - debug mode, all services on localhost",
            "production": "Production - hardened defaults, connection pooling",
            "docker": "Docker Compose - service names as hostnames",
            "minimal": "Minimal - single-process mode, no optional services",
        }
        for pname, desc in profiles.items():
            marker = _G if pname == name else _C
            print(f"  {marker}{pname:<16}{_R} {_dim(desc)}")
        print()
        print(f"  {_dim('Usage: mc_config.py profile <name>')}")
        return 0

    try:
        if name:
            profile = DeploymentProfile(name)
            profile.apply()
            print(f"  {_ok(f'Profile \"{name}\" applied')}")
        else:
            current = DeploymentProfile.detect()
            print(f"  Current profile: {_B}{current}{_R}")
            print("  Available: development, production, docker, minimal")
    except Exception as exc:
        print(f"  {_fail(f'Profile error: {exc}')}")
        return 1

    return 0


def cmd_setup(_args: argparse.Namespace) -> int:
    """Run the interactive setup wizard."""
    print(_heading("Mission Control - Setup Wizard"))
    print(_dim("This will guide you through the initial configuration.\n"))

    _setup_path()
    try:
        from app.setup.wizard import SetupWizard
    except ImportError:
        print(f"  {_fail('SetupWizard not importable - check backend/app/setup/wizard.py')}")
        return 1

    # Check if setup is needed
    needs_setup = True
    try:
        from app.db.database import SessionLocal
        from app.services.setup_service import is_setup_required

        db = SessionLocal()
        try:
            needs_setup = is_setup_required(db)
        finally:
            db.close()
    except Exception:
        print(f"  {_warn('Could not check database - proceeding anyway')}")

    if not needs_setup:
        print(f"  {_ok('Setup already complete - users exist in database')}")
        print(f"  {_dim('To re-run setup, reset the database first.')}")
        return 0

    # Collect configuration interactively
    print(f"  {_B}Step 1: Database Configuration{_R}\n")

    env = _read_env()
    pg_host = input(f"  PostgreSQL host [{env.get('postgres_host', 'localhost')}]: ").strip()
    pg_host = pg_host or env.get("postgres_host", "localhost")
    pg_port = input(f"  PostgreSQL port [{env.get('postgres_port', '5432')}]: ").strip()
    pg_port = pg_port or env.get("postgres_port", "5432")
    pg_user = input(f"  PostgreSQL user [{env.get('postgres_user', 'mission_control')}]: ").strip()
    pg_user = pg_user or env.get("postgres_user", "mission_control")
    pg_pass = input(f"  PostgreSQL password [{env.get('postgres_password', '')}]: ").strip()
    pg_pass = pg_pass or env.get("postgres_password", "")
    pg_db = input(f"  PostgreSQL database [{env.get('postgres_db', 'mission_control')}]: ").strip()
    pg_db = pg_db or env.get("postgres_db", "mission_control")

    print(f"\n  {_B}Step 2: Redis Configuration{_R}\n")

    redis_host = input(f"  Redis host [{env.get('redis_host', 'redis')}]: ").strip()
    redis_host = redis_host or env.get("redis_host", "redis")
    redis_port = input(f"  Redis port [{env.get('redis_port', '6379')}]: ").strip()
    redis_port = redis_port or env.get("redis_port", "6379")

    print(f"\n  {_B}Step 3: Secret Key{_R}\n")

    print(f"  {_dim('Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"')}")
    secret_key = input(f"  Secret key [{env.get('missioncontrol_secret_key', '')}]: ").strip()
    secret_key = secret_key or env.get("missioncontrol_secret_key", "")

    print(f"\n  {_B}Step 4: Validate Connections{_R}\n")

    # Validate
    wizard = SetupWizard.__new__(SetupWizard)
    pg_result = wizard.validate_postgres(
        host=pg_host,
        port=int(pg_port),
        user=pg_user,
        password=pg_pass,
        dbname=pg_db,
    )
    print(f"  PostgreSQL: {'OK' if pg_result['ok'] else 'FAIL'} - {pg_result['message']}")

    redis_result = wizard.validate_redis(host=redis_host, port=int(redis_port))
    print(f"  Redis:      {'OK' if redis_result['ok'] else 'FAIL'} - {redis_result['message']}")

    sk_result = wizard.validate_secret_key(secret_key)
    print(f"  Secret Key: {'OK' if sk_result['ok'] else 'FAIL'} - {sk_result['message']}")

    if not all([pg_result["ok"], redis_result["ok"], sk_result["ok"]]):
        print(f"\n  {_fail('Some validations failed. Fix issues and re-run setup.')}")
        return 1

    # Write .env
    final_env = dict(env)
    final_env["POSTGRES_HOST"] = pg_host
    final_env["POSTGRES_PORT"] = pg_port
    final_env["POSTGRES_USER"] = pg_user
    final_env["POSTGRES_PASSWORD"] = pg_pass
    final_env["POSTGRES_DB"] = pg_db
    final_env["REDIS_HOST"] = redis_host
    final_env["REDIS_PORT"] = redis_port
    if secret_key:
        final_env["MISSIONCONTROL_SECRET_KEY"] = secret_key

    _write_env(final_env)

    print(f"\n  {_ok('Configuration written to .env')}")
    print(f"  {_dim('Next: POST /api/v1/setup/bootstrap to create your admin account')}")
    return 0


# ------------------------------------------------------------------ #
# Argument parser                                                      #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mc_config",
        description="Mission Control CLI Configuration Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    sub.add_parser("version", help="Show version information")
    sub.add_parser("show", help="Display current configuration (secrets masked)")
    sub.add_parser("validate", help="Validate current configuration")
    sub.add_parser("edit", help="Open .env in editor")

    p_export = sub.add_parser("export", help="Export configuration to a file")
    p_export.add_argument("file", help="Destination file path")

    p_import = sub.add_parser("import", help="Import configuration from a file")
    p_import.add_argument("file", help="Source file path")

    sub.add_parser("doctor", help="Run full system diagnostics")

    p_reset = sub.add_parser("reset", help="Reset configuration to defaults")
    p_reset.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    p_profile = sub.add_parser("profile", help="Show or apply a deployment profile")
    p_profile.add_argument("profile_name", nargs="?", default="", help="Profile name")

    sub.add_parser("setup", help="Run interactive setup wizard")

    return parser


# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #

_COMMANDS = {
    "version": cmd_version,
    "show": cmd_show,
    "validate": cmd_validate,
    "edit": cmd_edit,
    "export": cmd_export,
    "import": cmd_import,
    "doctor": cmd_doctor,
    "reset": cmd_reset,
    "profile": cmd_profile,
    "setup": cmd_setup,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    handler = _COMMANDS.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        return 130
    except Exception as exc:
        print(f"{_Rd}Fatal error: {exc}{_R}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
