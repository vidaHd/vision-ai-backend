from __future__ import annotations

import logging

from celery.result import AsyncResult

from app.core.config import JOB_IDEMPOTENCY_TTL_SECONDS
from app.core.redis_client import get_redis
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_PREFIX = "vae:job:extract:"


def extract_job_key(filename: str) -> str:
    return f"{_PREFIX}{filename}"


def _job_is_reusable(job_id: str) -> bool:
    result = AsyncResult(job_id, app=celery_app)
    state = result.state or "PENDING"
    if state in {"PENDING", "STARTED", "PROGRESS", "RETRY"}:
        return True
    if state == "SUCCESS":
        return True
    return False


def get_existing_extract_job(filename: str) -> str | None:
    try:
        raw = get_redis().get(extract_job_key(filename))
    except Exception:
        logger.warning("Redis idempotency get failed for %s", filename, exc_info=True)
        return None
    if raw is None:
        return None
    job_id = raw.decode() if isinstance(raw, bytes) else str(raw)
    if not job_id:
        return None
    if _job_is_reusable(job_id):
        return job_id
    return None


def remember_extract_job(filename: str, job_id: str) -> None:
    try:
        get_redis().set(
            extract_job_key(filename),
            job_id,
            ex=JOB_IDEMPOTENCY_TTL_SECONDS,
        )
    except Exception:
        logger.warning(
            "Redis idempotency set failed for %s -> %s",
            filename,
            job_id,
            exc_info=True,
        )
