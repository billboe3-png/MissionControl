from redis.asyncio import Redis

from app.core.config import get_settings


async def check_redis() -> bool:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        return bool(await client.ping())
    finally:
        await client.aclose()
