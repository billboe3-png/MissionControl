import asyncpg

from app.core.config import get_settings


async def check_postgres() -> bool:
    settings = get_settings()
    connection = await asyncpg.connect(settings.database_url)
    try:
        value = await connection.fetchval("SELECT 1")
        return value == 1
    finally:
        await connection.close()
