from __future__ import annotations

from functools import lru_cache

import redis

from app.core.config import REDIS_URL


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    """Shared Redis client (same instance as Celery; we use `vae:` key prefixes)."""
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
