from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from app.core.config import CACHE_TTL_SECONDS
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_PREFIX = "vae:cache:"


def restaurants_list_key(user_id: UUID) -> str:
    return f"{_PREFIX}restaurants:list:{user_id}"


def restaurant_item_key(user_id: UUID, restaurant_id: UUID) -> str:
    return f"{_PREFIX}restaurants:item:{user_id}:{restaurant_id}"


def cache_get_json(key: str) -> Any | None:
    try:
        raw = get_redis().get(key)
    except Exception:
        logger.warning("Redis cache get failed for %s", key, exc_info=True)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set_json(key: str, value: Any, ttl: int | None = None) -> None:
    seconds = CACHE_TTL_SECONDS if ttl is None else ttl
    try:
        get_redis().set(key, json.dumps(value), ex=seconds)
    except Exception:
        logger.warning("Redis cache set failed for %s", key, exc_info=True)


def cache_delete(*keys: str) -> None:
    if not keys:
        return
    try:
        get_redis().delete(*keys)
    except Exception:
        logger.warning("Redis cache delete failed", exc_info=True)


def invalidate_user_restaurants(
    user_id: UUID,
    restaurant_id: UUID | None = None,
) -> None:
    """Drop list cache; also drop one item when id is known."""
    keys = [restaurants_list_key(user_id)]
    if restaurant_id is not None:
        keys.append(restaurant_item_key(user_id, restaurant_id))
    cache_delete(*keys)
