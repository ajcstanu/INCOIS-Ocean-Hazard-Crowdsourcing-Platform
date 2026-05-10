import json
from typing import Any, Optional
import redis.asyncio as aioredis
from loguru import logger
from config.settings import settings

_client: aioredis.Redis | None = None


async def connect_redis() -> None:
    """Initialize async Redis connection."""
    global _client
    try:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await _client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}). Caching disabled.")
        _client = None


async def disconnect_redis() -> None:
    """Close Redis connection."""
    global _client
    if _client:
        await _client.aclose()
        logger.info("Redis connection closed")


def get_client() -> aioredis.Redis | None:
    return _client


class Cache:
    """Async Redis cache wrapper. Silently no-ops when Redis is unavailable."""

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        if not _client:
            return None
        try:
            val = await _client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl_seconds: int = 300) -> None:
        if not _client:
            return
        try:
            await _client.setex(key, ttl_seconds, json.dumps(value, default=str))
        except Exception:
            pass

    @staticmethod
    async def delete(key: str) -> None:
        if not _client:
            return
        try:
            await _client.delete(key)
        except Exception:
            pass

    @staticmethod
    async def delete_pattern(pattern: str) -> None:
        if not _client:
            return
        try:
            keys = await _client.keys(pattern)
            if keys:
                await _client.delete(*keys)
        except Exception:
            pass

    @staticmethod
    async def exists(key: str) -> bool:
        if not _client:
            return False
        try:
            return bool(await _client.exists(key))
        except Exception:
            return False

    @staticmethod
    async def increment(key: str, ttl_seconds: int = 60) -> int:
        if not _client:
            return 0
        try:
            val = await _client.incr(key)
            if val == 1:
                await _client.expire(key, ttl_seconds)
            return val
        except Exception:
            return 0


cache = Cache()
