from redis.asyncio import Redis

from app.core.config import get_settings

_redis_client: Redis | None = None


def get_redis() -> Redis:
    """Return a shared Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def check_redis() -> bool:
    try:
        return bool(await get_redis().ping())
    except Exception:
        return False
