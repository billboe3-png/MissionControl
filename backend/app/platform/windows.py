from datetime import datetime, timezone
import subprocess

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis

from .base import PlatformBase


def run(command):

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.returncode == 0, result.stdout.strip()

    except Exception:
        return False, ""


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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def doctor(self):

        postgres = await check_postgres()
        redis = await check_redis()

        checks = [
            {
                "name":"Backend",
                "status":"OK",
                "message":"API running"
            },
            {
                "name":"PostgreSQL",
                "status":"OK" if postgres else "ERROR",
                "message":"Connected" if postgres else "Unavailable"
            },
            {
                "name":"Redis",
                "status":"OK" if redis else "ERROR",
                "message":"Connected" if redis else "Unavailable"
            }
        ]

        return {
            "overall":"healthy" if postgres and redis else "degraded",
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "checks":checks
        }

    async def docker_status(self):

        engine,_ = run(["docker","info"])

        compose,_ = run(["docker","compose","version"])

        return {
            "engine":"running" if engine else "offline",
            "compose":"available" if compose else "missing"
        }
