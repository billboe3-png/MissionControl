from datetime import UTC, datetime

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis
from app.infrastructure.docker import get_docker_provider

from .base import PlatformBase


class WindowsPlatform(PlatformBase):
    async def status(self):

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
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def doctor(self):

        postgres = await check_postgres()
        redis = await check_redis()

        checks = [
            {
                "name": "Backend",
                "status": "OK",
                "message": "API running",
            },
            {
                "name": "PostgreSQL",
                "status": "OK" if postgres else "ERROR",
                "message": "Connected" if postgres else "Unavailable",
            },
            {
                "name": "Redis",
                "status": "OK" if redis else "ERROR",
                "message": "Connected" if redis else "Unavailable",
            },
        ]

        return {
            "overall": "healthy" if postgres and redis else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        }

    async def docker_status(self):

        docker = get_docker_provider()

        version = await docker.version()
        containers = await docker.containers()

        return {
            "engine": "running" if version else "offline",
            "compose": "sdk",
            "container_count": len(containers),
            "containers": containers,
            "docker_version": version.get("Version", "Unknown"),
        }
