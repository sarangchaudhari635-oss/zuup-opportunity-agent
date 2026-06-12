"""
Redis client singleton for caching and rate limiting.
"""
import redis.asyncio as aioredis
import redis as sync_redis
from app.core.config import settings

# Async Redis client (for FastAPI endpoints)
_async_redis: aioredis.Redis | None = None

# Sync Redis client (for Celery workers)
_sync_redis: sync_redis.Redis | None = None


def get_async_redis() -> aioredis.Redis:
    global _async_redis
    if _async_redis is None:
        _async_redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _async_redis


def get_sync_redis() -> sync_redis.Redis:
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = sync_redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _sync_redis


# Cache TTLs (in seconds)
CACHE_TTL = {
    "opportunity_feed": 15 * 60,      # 15 minutes
    "opportunity_detail": 60 * 60,    # 1 hour
    "student_profile": 5 * 60,        # 5 minutes
    "notifications": 2 * 60,          # 2 minutes
}


async def cache_get(key: str) -> str | None:
    r = get_async_redis()
    return await r.get(key)


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    r = get_async_redis()
    await r.setex(key, ttl, value)


async def cache_delete(key: str) -> None:
    r = get_async_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    r = get_async_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)
