"""Async Redis client for session management.

Falls back to DB-only token validation when Redis is unreachable.
"""

from __future__ import annotations

from app.utils.logger import logger
from app.config import settings

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None  # type: ignore[assignment]

_SESSION_PREFIX = "session:"


class RedisClient:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None  # type: ignore[name-defined]
        self._available = False

    async def connect(self) -> None:
        if aioredis is None:
            logger.warning("redis package not installed; running without session cache")
            return
        try:
            self._redis = aioredis.from_url(
                settings.redis_url, decode_responses=True
            )
            await self._redis.ping()
            self._available = True
            logger.info("redis_connected url=%s", settings.redis_url)
        except Exception as exc:
            logger.warning("redis_unavailable error=%s — falling back to DB-only auth", exc)
            self._redis = None
            self._available = False

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def create_session(
        self, user_id: str, auth_token: str, ttl_seconds: int
    ) -> None:
        if not self._available or not self._redis:
            return
        try:
            await self._redis.setex(
                f"{_SESSION_PREFIX}{auth_token}", ttl_seconds, user_id
            )
        except Exception as exc:
            logger.warning("redis_set_failed token=%s error=%s", auth_token[:8], exc)

    async def get_session(self, auth_token: str) -> str | None:
        if not self._available or not self._redis:
            return None
        try:
            return await self._redis.get(f"{_SESSION_PREFIX}{auth_token}")
        except Exception:
            return None

    async def delete_session(self, auth_token: str) -> None:
        if not self._available or not self._redis:
            return
        try:
            await self._redis.delete(f"{_SESSION_PREFIX}{auth_token}")
        except Exception:
            pass

    async def delete_sessions(self, auth_tokens: list[str]) -> None:
        """Remove multiple session keys from Redis (bulk invalidation)."""
        if not self._available or not self._redis or not auth_tokens:
            return
        try:
            keys = [f"{_SESSION_PREFIX}{t}" for t in auth_tokens]
            await self._redis.delete(*keys)
        except Exception as exc:
            logger.warning("redis_bulk_delete_failed count=%d error=%s", len(auth_tokens), exc)


redis_client = RedisClient()
