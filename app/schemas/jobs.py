from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.menu import MenuExtractResponse

JobStatus = Literal["queued", "processing", "succeeded", "failed"]


class ExtractJobRequest(BaseModel):
    filename: str = Field(..., min_length=1)


class ExtractJobCreated(BaseModel):
    job_id: str
    status: JobStatus = "queued"


class ExtractJobStatus(BaseModel):
    job_id: str
    status: JobStatus
    stage: str | None = None
    message: str | None = None
    result: MenuExtractResponse | None = None
    error: str | None = None
    # Raw Celery state for debugging / learning
    celery_state: str | None = None
    meta: dict[str, Any] | None = None
