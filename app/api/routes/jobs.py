from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Request

from app.core.config import RATE_LIMIT_EXTRACT, RATE_LIMIT_WINDOW_SECONDS
from app.schemas.jobs import (
    ExtractJobCreated,
    ExtractJobRequest,
    ExtractJobStatus,
    JobStatus,
)
from app.schemas.menu import MenuExtractResponse
from app.services.job_idempotency import get_existing_extract_job, remember_extract_job
from app.services.ocr.service import resolve_upload_path
from app.services.rate_limit import client_ip, enforce_rate_limit
from app.workers.celery_app import celery_app
from app.workers.tasks import extract_menu_pipeline

router = APIRouter(tags=["jobs"])


def _map_status(celery_state: str) -> JobStatus:
    if celery_state in {"PENDING"}:
        return "queued"
    if celery_state in {"STARTED", "PROGRESS", "RETRY"}:
        return "processing"
    if celery_state == "SUCCESS":
        return "succeeded"
    # FAILURE, REVOKED, and anything unexpected
    return "failed"


def _error_message(result: AsyncResult) -> str:
    info = result.info
    if isinstance(info, Exception):
        return str(info)
    if isinstance(info, dict):
        exc_message = info.get("exc_message")
        if isinstance(exc_message, list) and exc_message:
            return str(exc_message[0])
        if isinstance(exc_message, str):
            return exc_message
        message = info.get("message")
        if isinstance(message, str):
            return message
    if info is not None:
        return str(info)
    return "Job failed"


@router.post("/jobs/extract", response_model=ExtractJobCreated)
def enqueue_extract_job(
    body: ExtractJobRequest,
    request: Request,
) -> ExtractJobCreated:
    """Enqueue OCR + menu extraction; returns immediately with a job id."""
    enforce_rate_limit(
        scope="extract",
        identity=client_ip(request),
        limit=RATE_LIMIT_EXTRACT,
        window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    )
    try:
        resolve_upload_path(body.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    existing_job_id = get_existing_extract_job(body.filename)
    if existing_job_id:
        return ExtractJobCreated(job_id=existing_job_id, status="queued")

    task = extract_menu_pipeline.delay(body.filename)
    remember_extract_job(body.filename, task.id)
    return ExtractJobCreated(job_id=task.id, status="queued")


@router.get("/jobs/{job_id}", response_model=ExtractJobStatus)
def get_extract_job(job_id: str) -> ExtractJobStatus:
    """Poll Celery for job progress / final menu result."""
    result = AsyncResult(job_id, app=celery_app)
    celery_state = result.state or "PENDING"
    status = _map_status(celery_state)

    stage: str | None = None
    message: str | None = None
    meta: dict | None = None
    menu: MenuExtractResponse | None = None
    error: str | None = None

    if status == "queued":
        message = "Queued for extraction…"
    elif status == "processing":
        info = result.info if isinstance(result.info, dict) else {}
        meta = info
        stage = info.get("stage") if isinstance(info.get("stage"), str) else None
        message = (
            info.get("message")
            if isinstance(info.get("message"), str)
            else "Processing…"
        )
    elif status == "succeeded":
        raw = result.result
        if not isinstance(raw, dict):
            raise HTTPException(
                status_code=500,
                detail="Job succeeded but result payload is invalid",
            )
        try:
            menu = MenuExtractResponse.model_validate(raw)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Job result failed validation: {exc}",
            ) from exc
        message = "Done"
        stage = "done"
    else:
        error = _error_message(result)
        message = error
        if isinstance(result.info, dict):
            meta = result.info

    return ExtractJobStatus(
        job_id=job_id,
        status=status,
        stage=stage,
        message=message,
        result=menu,
        error=error,
        celery_state=celery_state,
        meta=meta,
    )
