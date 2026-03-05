"""
Rate Limiter - Per-domain token bucket rate limiting.

Ensures we respect rate limits per domain, preventing abuse and
complying with robots.txt throttle requirements.
"""

import asyncio
import time
from collections import defaultdict
from urllib.parse import urlparse

from app.utils.logger import logger


class TokenBucket:
    """Token bucket rate limiter for a single domain."""

    def __init__(self, rate_rpm: int = 10):
        self.rate = rate_rpm / 60.0  # Tokens per second
        self.max_tokens = max(rate_rpm / 6, 2)  # Burst capacity (10s worth)
        self.tokens = self.max_tokens
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a token is available, then consume one."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                logger.debug("rate_limit_wait wait_seconds=%.2f", wait_time)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class RateLimiter:
    """Manages per-domain rate limiting using token buckets."""

    def __init__(self, default_rpm: int = 10):
        self.default_rpm = default_rpm
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc or parsed.path

    async def acquire(self, url: str, rpm: int | None = None):
        """Acquire a rate limit token for the given URL's domain."""
        domain = self._get_domain(url)
        async with self._lock:
            if domain not in self._buckets:
                self._buckets[domain] = TokenBucket(rpm or self.default_rpm)

        await self._buckets[domain].acquire()

    def set_domain_rate(self, domain: str, rpm: int):
        """Set a custom rate limit for a specific domain."""
        self._buckets[domain] = TokenBucket(rpm)


# Singleton rate limiter
rate_limiter = RateLimiter()
