from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis


async def get_status() -> dict:
    settings = get_settings()

    postgres = await check_postgres()
    redis = await check_redis()

    return {
        "project": settings.project_name,
        "environment": settings.environment,
        "version": "0.1.0",
        "backend": "online",
        "database": "connected" if postgres else "disconnected",
        "redis": "connected" if redis else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
