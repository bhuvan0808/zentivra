"""Valkey client — async Valkey/Redis client for session management.

Stores session data keyed by auth_token. Falls back to DB-only token validation
when Valkey is unreachable. Uses the redis.asyncio library (wire-compatible with Valkey).

Session JSON structure stored per key:
  {
    "id": int,           # User primary key
    "user_id": str,      # User UUID
    "session_id": str,   # Session identifier
    "expires_at": str    # ISO datetime string
  }
"""

from __future__ import annotations

import json

from app.utils.logger import logger
from app.config import settings

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None  # type: ignore[assignment]

_SESSION_PREFIX = "session:"


class ValkeyClient:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None  # type: ignore[name-defined]
        self._available = False

    async def connect(self) -> None:
        """Connect to Valkey. Sets _available=False if redis not installed or connection fails."""
        if aioredis is None:
            logger.warning("redis package not installed; running without session cache")
            return
        try:
            self._redis = aioredis.from_url(settings.valkey_url, decode_responses=True)
            await self._redis.ping()
            self._available = True
            logger.info("valkey_connected url=%s", settings.valkey_url)
        except Exception as exc:
            logger.warning(
                "valkey_unavailable error=%s — falling back to DB-only auth", exc
            )
            self._redis = None
            self._available = False

    async def close(self) -> None:
        """Close the Valkey connection and set _available=False."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            self._available = False

    @property
    def available(self) -> bool:
        """True if Valkey is connected and usable."""
        return self._available

    async def create_session(
        self,
        user_pk: int,
        user_uuid: str,
        session_id: str,
        auth_token: str,
        ttl_seconds: int,
        expires_at: str,
    ) -> None:
        """Store session JSON at session:{auth_token} with TTL. No-op if Valkey unavailable."""
        if not self._available or not self._redis:
            return
        try:
            payload = json.dumps(
                {
                    "id": user_pk,
                    "user_id": user_uuid,
                    "session_id": session_id,
                    "expires_at": expires_at,
                }
            )
            await self._redis.setex(
                f"{_SESSION_PREFIX}{auth_token}", ttl_seconds, payload
            )
        except Exception as exc:
            logger.warning("valkey_set_failed token=%s error=%s", auth_token[:8], exc)

    async def get_session(self, auth_token: str) -> dict | None:
        """Return parsed session dict (id, user_id, session_id, expires_at) or None if not found or unavailable."""
        if not self._available or not self._redis:
            return None
        try:
            raw = await self._redis.get(f"{_SESSION_PREFIX}{auth_token}")
            if raw:
                return json.loads(raw)
            return None
        except Exception:
            return None

    async def delete_session(self, auth_token: str) -> None:
        """Remove session key for the given auth token. No-op if Valkey unavailable."""
        if not self._available or not self._redis:
            return
        try:
            await self._redis.delete(f"{_SESSION_PREFIX}{auth_token}")
        except Exception:
            pass

    async def delete_sessions(self, auth_tokens: list[str]) -> None:
        """Remove multiple session keys from Valkey (bulk invalidation). No-op if Valkey unavailable or empty list."""
        if not self._available or not self._redis or not auth_tokens:
            return
        try:
            keys = [f"{_SESSION_PREFIX}{t}" for t in auth_tokens]
            await self._redis.delete(*keys)
        except Exception as exc:
            logger.warning(
                "valkey_bulk_delete_failed count=%d error=%s", len(auth_tokens), exc
            )


# Singleton Valkey client for session management
valkey_client = ValkeyClient()
