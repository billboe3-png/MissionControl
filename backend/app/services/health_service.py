"""
Mission Control Health Service

Provides health information for the dashboard.

Sprint:
    1.0.3 - Dashboard Service Refactor
"""

from app.db.postgres import check_postgres
from app.db.redis import check_redis


class HealthService:
    """Health dashboard section."""

    async def get_data(self) -> dict:
        """Return live health information."""

        postgres = await check_postgres()
        redis = await check_redis()

        return {
            "backend": {
                "status": "healthy",
            },
            "database": {
                "status": "healthy" if postgres else "offline",
            },
            "redis": {
                "status": "healthy" if redis else "offline",
            },
        }


health_service = HealthService()
