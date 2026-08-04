from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_PREFIX = "vae:rl:"


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(
    *,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int,
) -> None:
    """
    Fixed-window counter in Redis.
    Raises HTTP 429 when `identity` exceeds `limit` hits inside `window_seconds`.
    If Redis is unreachable, allow the request (local-dev friendly).
    """
    if limit <= 0:
        return

    key = f"{_PREFIX}{scope}:{identity}"
    try:
        r = get_redis()
        count = int(r.incr(key))
        if count == 1:
            r.expire(key, window_seconds)
    except Exception:
        logger.warning("Rate limit check failed; allowing request", exc_info=True)
        return

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Too many {scope} requests. "
                f"Limit is {limit} per {window_seconds}s. Try again shortly."
            ),
        )
