"""
PostgreSQL async health check.

asyncpg only accepts postgresql:// DSNs.
SQLAlchemy uses postgresql+psycopg:// DSNs.
This module bridges the two by stripping the driver suffix.
"""

import logging

import asyncpg

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def check_postgres() -> bool:
    """
    Ping PostgreSQL via asyncpg and return True if healthy.

    The SQLAlchemy DSN uses the psycopg driver suffix
    (postgresql+psycopg://) which asyncpg does not recognise.
    We strip the driver suffix so asyncpg receives a plain
    postgresql:// scheme.
    """
    settings = get_settings()

    async_dsn = settings.database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
    )

    connection = None
    try:
        connection = await asyncpg.connect(async_dsn)
        value = await connection.fetchval("SELECT 1")
        return value == 1
    except Exception:
        logger.warning("PostgreSQL health check failed")
        return False
    finally:
        if connection is not None:
            await connection.close()
