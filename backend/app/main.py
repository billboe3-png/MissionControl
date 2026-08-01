import logging
import os
import time
import asyncio
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging_config import (
    clear_context,
    generate_request_id,
    set_request_id,
    setup_logging,
)

_TESTING = os.getenv("TESTING", "0") == "1"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware using sliding windows."""

    def __init__(
        self,
        app,
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

        # Login is rate-limited per client + account (not just per IP). Behind
        # the nginx reverse proxy every request appears to come from the proxy
        # IP, so a plain per-IP bucket would lock out ALL users after a handful
        # of attempts. Keying on the target email keeps each account's budget
        # isolated and prevents one client from blocking everyone.
        if path == "/api/v1/auth/login":
            key = f"{ip}|login|{await self._login_identity(request)}"
            limit = self.auth_limit
        else:
            key = ip
            limit = self.default_limit

        self._requests[key] = [t for t in self._requests.get(key, []) if t > cutoff]
        timestamps = self._requests[key]

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

    async def _login_identity(self, request: Request) -> str:
        """Best-effort extraction of the login identifier for rate-limit keying.

        Awaits (and caches) the request body so the downstream route can still
        parse it. Falls back to an empty string if not parseable.
        """
        try:
            body = await request.body()
            import json as _json

            data = _json.loads(body)
            ident = data.get("email") or data.get("username") or ""
            return str(ident).strip().lower()
        except Exception:
            return ""

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
    marketplace,
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
    version="3.0.0-rc1",
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
        "%s %s %s %sms",
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
app.include_router(marketplace.router, prefix="/api/v1")


@app.get("/api/v1")
async def api_root() -> dict[str, str]:
    """
    Mission Control API Root
    """
    return {
        "name": settings.project_name,
        "status": "online",
        "version": "3.0.0-rc1",
    }


@app.on_event("startup")
async def _startup_banner():
    """Run startup validation, load plugins, and print status banner."""
    from app.db.database import SessionLocal
    from app.services.setup_service import is_setup_required

    print("")
    print("  Mission Control v3.0.0-rc1")
    print("  ─────────────────────────────────────")

    # Run comprehensive startup validation
    try:
        from app.core.startup_check import print_startup_report, run_all_checks

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

    # Load and start server plugins
    try:
        from app.plugins.registry import plugin_registry

        load_results = await plugin_registry.discover_and_load()
        loaded = [s for s, r in load_results.items() if r == "loaded"]
        if loaded:
            logger.info("Plugins discovered: %s", ", ".join(loaded))
            await plugin_registry.setup_all()
            await plugin_registry.start_all()
            route_count = await plugin_registry.register_routes(app)
            logger.info(
                "Plugins started: %d, routes registered: %d",
                len(loaded),
                route_count,
            )
            print(f"  Plugins: {len(loaded)} loaded, {route_count} routes")

            # Auto-register built-in plugins in marketplace registry
            try:
                from app.marketplace.registry import (
                    InstalledPlugin,
                    PluginHealth,
                    PluginStatus,
                    marketplace_registry,
                )
                for slug in loaded:
                    if not marketplace_registry.get(slug):
                        from app.services.plugin_marketplace_service import (
                            plugin_marketplace_service,
                        )
                        info = plugin_marketplace_service.get_plugin_info(slug)
                        installed = InstalledPlugin(
                            plugin_id=slug,
                            name=info["name"] if info else slug,
                            version=info["version"] if info else "1.0.0",
                            status=PluginStatus.ENABLED,
                            health=PluginHealth.UNKNOWN,
                            enabled=True,
                        )
                        marketplace_registry.register(installed)
            except Exception:
                pass
        else:
            print("  Plugins: none discovered")
    except Exception as exc:
        logger.warning("Plugin loading skipped: %s", exc)
        print("  Plugins: skipped (error)")

    # Mark stale agents offline on a fixed interval
    try:
        from app.services.agent_service import AgentService

        agent_service = AgentService()

        async def _stale_sweeper():
            while True:
                try:
                    db = SessionLocal()
                    try:
                        await agent_service.mark_stale_agents_offline(db)
                    finally:
                        db.close()
                except Exception as exc:
                    logger.warning("Stale agent sweep failed: %s", exc)
                await asyncio.sleep(60)

        _startup_task = asyncio.create_task(_stale_sweeper())
        logger.info("Stale-agent sweeper started")
    except Exception as exc:
        logger.warning("Stale-agent sweaper failed to start: %s", exc)

    print("")


@app.on_event("shutdown")
async def _shutdown_plugins():
    """Gracefully stop all running plugins."""
    try:
        from app.plugins.registry import plugin_registry

        await plugin_registry.stop_all()
    except Exception:
        pass
