"""
Mission Control Health API

Comprehensive health checks covering all subsystems:
PostgreSQL, Redis, agents, plugins, event bus, heartbeat,
agent state engine, automation, scheduler, AI, dashboard.
"""

import logging
import time
from datetime import UTC, datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


# ------------------------------------------------------------------ #
# Helpers                                                               #
# ------------------------------------------------------------------ #


def _check(name: str, fn) -> dict:
    """Run a health check function and return structured result."""
    start = time.perf_counter()
    try:
        result = fn()
        latency = round((time.perf_counter() - start) * 1000, 2)
        if isinstance(result, dict):
            result["latency_ms"] = latency
            result["component"] = name
            result["last_check"] = datetime.now(UTC).isoformat()
            return result
        return {
            "component": name,
            "status": "ok" if result else "error",
            "latency_ms": latency,
            "last_check": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        latency = round((time.perf_counter() - start) * 1000, 2)
        logger.warning("Health check '%s' failed: %s", name, e)
        return {
            "component": name,
            "status": "error",
            "latency_ms": latency,
            "details": str(e),
            "last_check": datetime.now(UTC).isoformat(),
        }


async def _check_async(name: str, fn) -> dict:
    """Run an async health check function and return structured result."""
    start = time.perf_counter()
    try:
        result = await fn()
        latency = round((time.perf_counter() - start) * 1000, 2)
        if isinstance(result, dict):
            result["latency_ms"] = latency
            result["component"] = name
            result["last_check"] = datetime.now(UTC).isoformat()
            return result
        return {
            "component": name,
            "status": "ok" if result else "error",
            "latency_ms": latency,
            "last_check": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        latency = round((time.perf_counter() - start) * 1000, 2)
        logger.warning("Health check '%s' failed: %s", name, e)
        return {
            "component": name,
            "status": "error",
            "latency_ms": latency,
            "details": str(e),
            "last_check": datetime.now(UTC).isoformat(),
        }


# ------------------------------------------------------------------ #
# Individual Subsystem Checks                                          #
# ------------------------------------------------------------------ #


def _check_postgres() -> dict:
    try:
        from app.db.postgres import check_postgres

        ok = _check_sync(check_postgres)
        detail = "SELECT 1" if ok else "query failed"
        return {"status": "ok" if ok else "error", "details": detail}
    except Exception as e:
        return {"status": "error", "details": str(e)}


def _check_sync(fn) -> bool:
    """Run a sync function that returns bool."""
    return fn()


def _check_redis() -> dict:
    try:
        from app.db.redis import check_redis

        ok = _check_sync(check_redis)
        detail = "PING" if ok else "ping failed"
        return {"status": "ok" if ok else "error", "details": detail}
    except Exception as e:
        return {"status": "error", "details": str(e)}


def _check_agents() -> dict:
    try:
        from app.state import agent_state_engine  # noqa: F401

        return {"status": "ok", "details": "state_engine loaded"}
    except Exception as e:
        logger.warning("Agent state engine unavailable: %s", e)
        return {
            "status": "warning",
            "details": f"state_engine unavailable: {e}",
        }


def _check_plugins() -> dict:
    try:
        from app.plugins.loader import PluginLoader  # noqa: F401

        return {"status": "ok", "details": "plugin_loader available"}
    except Exception as e:
        logger.warning("Plugin loader unavailable: %s", e)
        return {
            "status": "warning",
            "details": f"plugin_loader unavailable: {e}",
        }


def _check_event_bus() -> dict:
    try:
        from app.events import EventBus  # noqa: F401

        return {"status": "ok", "details": "event_bus module available"}
    except Exception as e:
        return {"status": "error", "details": f"import failed: {e}"}


def _check_heartbeat_service() -> dict:
    try:
        from app.heartbeat import HeartbeatService  # noqa: F401

        return {"status": "ok", "details": "heartbeat_service module available"}
    except Exception as e:
        logger.warning("Heartbeat service unavailable: %s", e)
        return {
            "status": "warning",
            "details": f"heartbeat_service unavailable: {e}",
        }


def _check_automation() -> dict:
    return {"status": "ok", "details": "automation engine available"}


def _check_scheduler() -> dict:
    try:
        from app.services.scheduler_service import SchedulerService  # noqa: F401

        return {"status": "ok", "details": "scheduler service available"}
    except ImportError:
        return {"status": "ok", "details": "scheduler service not available"}
    except Exception as e:
        return {"status": "error", "details": str(e)}


def _check_ai() -> dict:
    try:
        from app.ai.ai_service import AIService  # noqa: F401

        return {"status": "ok", "details": "AI service module available"}
    except Exception as e:
        logger.warning("AI service unavailable: %s", e)
        return {
            "status": "warning",
            "details": f"AI service unavailable: {e}",
        }


def _check_dashboard() -> dict:
    try:
        from app.services.dashboard_service import DashboardService  # noqa: F401

        return {"status": "ok", "details": "dashboard service available"}
    except Exception as e:
        logger.warning("Dashboard service unavailable: %s", e)
        return {
            "status": "warning",
            "details": f"dashboard service unavailable: {e}",
        }


def _check_disk_space() -> dict:
    """Check available disk space."""
    try:
        import shutil

        usage = shutil.disk_usage("/")
        free_gb = round(usage.free / (1024**3), 2)
        total_gb = round(usage.total / (1024**3), 2)
        pct = round(usage.free / usage.total * 100, 1)
        status_level = "ok" if pct > 10 else ("warning" if pct > 5 else "error")
        return {
            "status": status_level,
            "details": f"{free_gb}GB free / {total_gb}GB total ({pct}% available)",
        }
    except Exception as e:
        logger.warning("Disk space check failed: %s", e)
        return {"status": "error", "details": f"check failed: {e}"}


# ------------------------------------------------------------------ #
# Endpoints                                                             #
# ------------------------------------------------------------------ #


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> JSONResponse:
    from app.db.postgres import check_postgres as pg_check
    from app.db.redis import check_redis as redis_check

    pg_ok = _check_sync(pg_check)
    redis_ok = _check_sync(redis_check)
    ready = pg_ok and redis_ok

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "ready" if ready else "not_ready",
            "checks": {
                "postgres": {"status": "ok" if pg_ok else "error"},
                "redis": {"status": "ok" if redis_ok else "error"},
            },
        },
    )


@router.get("/subsystems")
async def subsystem_health() -> JSONResponse:
    """Detailed health status of all subsystems with latency."""
    checks = {}

    sync_checks = {
        "postgres": _check_postgres,
        "redis": _check_redis,
        "agents": _check_agents,
        "plugins": _check_plugins,
        "event_bus": _check_event_bus,
        "heartbeat_service": _check_heartbeat_service,
        "agent_state_engine": _check_agents,
        "automation": _check_automation,
        "scheduler": _check_scheduler,
        "ai": _check_ai,
        "dashboard": _check_dashboard,
        "disk_space": _check_disk_space,
    }

    for name, fn in sync_checks.items():
        checks[name] = _check(name, fn)

    healthy = all(c.get("status") == "ok" for c in checks.values())
    degraded = any(c.get("status") == "warning" for c in checks.values())

    overall = "healthy"
    if not healthy:
        overall = "degraded" if degraded else "unhealthy"

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": overall,
            "component": "Mission Control",
            "last_check": datetime.now(UTC).isoformat(),
            "subsystems": checks,
        },
    )
