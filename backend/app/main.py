import logging
import os
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging_config import (
    clear_context,
    generate_request_id,
    set_request_id,
    setup_logging,
)
from app.core.error_handlers import register_error_handlers

_TESTING = os.getenv("TESTING", "0") == "1"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware using sliding windows."""

    def __init__(
        self,
        app,  # noqa: B008
        default_limit: int = 60,
        auth_limit: int = 5,
        window: int = 60,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self) -> None:
        now = time.time()
        if now - self._last_cleanup < self.window:
            return
        self._last_cleanup = now
        cutoff = now - self.window
        stale = [k for k, v in self._requests.items() if not v or v[-1] < cutoff]
        for k in stale:
            del self._requests[k]

    async def dispatch(self, request: Request, call_next):
        if _TESTING:
            return await call_next(request)

        path = request.url.path
        if any(
            path.startswith(p)
            for p in (
                "/api/v1/health", "/api/v1/version",
                "/api/v1/agents/", "/api/v1/setup",
            )
        ):
            return await call_next(request)

        self._cleanup()
        ip = self._client_ip(request)
        now = time.time()
        cutoff = now - self.window

        limit = self.auth_limit if path == "/api/v1/auth/login" else self.default_limit

        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]
        timestamps = self._requests[ip]

        remaining = max(0, limit - len(timestamps))

        if len(timestamps) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(self.window),
                },
            )

        timestamps.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        return response

setup_logging(level="INFO")
logger = logging.getLogger("missioncontrol")
from app.routers import (  # noqa: E402
    agent,
    agent_remote_target,
    agent_token,
    ai,
    auth,
    automation,
    company,
    dashboard,
    health,
    hyperv,
    identity,
    integration,
    notes,
    parking_lot,
    plugin,
    projects,
    proxmox,
    remote,
    resume,
    setup,
    site,
    tasks,
    veeam,
    version,
    zabbix,
)

try:
    settings = get_settings()
except Exception as exc:
    from app.core.startup_check import _fail

    _fail(
        message=f"Configuration error: {exc}",
        instruction=(
            "Check your .env file and ensure MISSIONCONTROL_SECRET_KEY "
            "is set to a valid Fernet key.\n"
            "\n"
            "Generate one using:\n"
            "\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        ),
    )

app = FastAPI(
    title=settings.project_name,
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Attach request ID and log every request with timing."""
    request_id = request.headers.get("X-Request-ID", generate_request_id())
    set_request_id(request_id)
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s %s %sms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    clear_context()
    return response


app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Agent-API-Key"],
)

# Register consistent error handlers
register_error_handlers(app)

# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------

app.include_router(health.router, prefix="/api/v1")
app.include_router(version.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")
app.include_router(resume.router, prefix="/api/v1")
app.include_router(parking_lot.router, prefix="/api/v1")
app.include_router(remote.router, prefix="/api/v1")
app.include_router(identity.router, prefix="/api/v1")
app.include_router(integration.router, prefix="/api/v1")
app.include_router(zabbix.router, prefix="/api/v1")
app.include_router(hyperv.router, prefix="/api/v1")
app.include_router(proxmox.router, prefix="/api/v1")
app.include_router(veeam.router, prefix="/api/v1")
app.include_router(site.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(agent_remote_target.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
app.include_router(company.router, prefix="/api/v1")
app.include_router(setup.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(agent_token.router, prefix="/api/v1")
app.include_router(plugin.router, prefix="/api/v1")


@app.get("/api/v1")
async def api_root() -> dict[str, str]:
    """
    Mission Control API Root
    """
    return {
        "name": settings.project_name,
        "status": "online",
        "version": "3.0.0",
    }


@app.on_event("startup")
async def _startup_banner():
    """Run startup validation and print status banner."""
    from app.db.database import SessionLocal
    from app.services.setup_service import is_setup_required

    print("")
    print("  Mission Control v3.0.0")
    print("  ─────────────────────────────────────")

    # Run comprehensive startup validation
    try:
        from app.core.startup_check import run_all_checks, print_startup_report

        results = run_all_checks()
        print_startup_report(results)

        critical = [r for r in results if not r.ok and r.critical]
        if critical:
            logger.error("Startup validation failed: %d critical errors", len(critical))
            for r in critical:
                logger.error("  CRIT: %s - %s", r.name, r.message)
    except Exception as exc:
        logger.warning("Startup validation skipped: %s", exc)

    # Check setup status
    try:
        db = SessionLocal()
        try:
            if is_setup_required(db):
                print("  Setup Required: YES")
                print("  Waiting for administrator bootstrap...")
            else:
                print("  Setup Required: NO")
                print("  Starting Platform...")
        finally:
            db.close()
    except Exception:
        print("  Setup Required: UNKNOWN (database not reachable)")
    print("")
