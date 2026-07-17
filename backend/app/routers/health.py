import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.postgres import check_postgres
from app.db.redis import check_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> JSONResponse:
    checks = {
        "postgres": await check_postgres(),
        "redis": await check_redis(),
    }
    ready = all(checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )
