"""
Mission Control Health Provider

Verifies live connectivity for Backend, PostgreSQL, and Redis.
No hardcoded values.
"""

import logging

from sqlalchemy.orm import Session

from app.db.postgres import check_postgres
from app.db.redis import check_redis
from app.repositories.dashboard_repository import dashboard_repository

logger = logging.getLogger(__name__)


class HealthProvider:
    """Return live health status for infrastructure services."""

    async def get_health(self, db: Session) -> dict:
        """
        Return health status for backend, database, and redis.

        Backend is healthy if this code is executing.
        Database is healthy if the SELECT 1 ping succeeds.
        Redis is healthy if the PING command succeeds.
        """
        postgres_ok = await check_postgres()
        redis_ok = await check_redis()

        project_count = dashboard_repository.count_projects(db)

        return {
            "backend": {
                "status": "healthy",
                "message": "API responding normally",
            },
            "database": {
                "status": "healthy" if postgres_ok else "unhealthy",
                "message": "Connected" if postgres_ok else "Connection failed",
                "project_count": project_count,
            },
            "redis": {
                "status": "healthy" if redis_ok else "unhealthy",
                "message": "Connected" if redis_ok else "Connection failed",
            },
        }


health_provider = HealthProvider()
