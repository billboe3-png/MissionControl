from datetime import datetime, timezone

from app.db.postgres import check_postgres
from app.db.redis import check_redis


async def get_doctor() -> dict:

    postgres = await check_postgres()
    redis = await check_redis()

    checks = [
        {
            "name": "Backend",
            "status": "OK",
            "message": "API running"
        },
        {
            "name": "PostgreSQL",
            "status": "OK" if postgres else "ERROR",
            "message": "Connected" if postgres else "Unavailable"
        },
        {
            "name": "Redis",
            "status": "OK" if redis else "ERROR",
            "message": "Connected" if redis else "Unavailable"
        }
    ]

    overall = "healthy"

    if not postgres or not redis:
        overall = "degraded"

    return {
        "overall": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks
    }
