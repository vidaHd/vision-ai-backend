from __future__ import annotations

from typing import Any

from app.core.config import TASK_MAX_RETRIES
from app.schemas.menu import (
    MenuExtractLine,
    MenuExtractRequest,
    MenuExtractResponse,
    OcrEcho,
)
from app.services.llm.provider import LLMProviderError, LLMTimeoutError
from app.services.menu.service import extract_menu
from app.services.ocr.service import run_ocr
from app.workers.celery_app import celery_app

_RETRYABLE = (LLMTimeoutError, LLMProviderError, ConnectionError, TimeoutError, OSError)


@celery_app.task(
    bind=True,
    name="extract_menu_pipeline",
    autoretry_for=_RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=TASK_MAX_RETRIES,
)
def extract_menu_pipeline(self, filename: str) -> dict[str, Any]:
    """Run OCR then LLM menu structuring; report progress via Celery state."""
    retry_note = ""
    if self.request.retries > 0:
        retry_note = f" (retry {self.request.retries}/{TASK_MAX_RETRIES})"

    self.update_state(
        state="PROGRESS",
        meta={"stage": "ocr", "message": f"Reading the menu…{retry_note}"},
    )
    ocr = run_ocr(filename)

    if not ocr.lines:
        empty = MenuExtractResponse(
            categories=[],
            currency=None,
            ocr=OcrEcho(lines=[], full_text=""),
            warnings=[],
        )
        return empty.model_dump(mode="json")

    self.update_state(
        state="PROGRESS",
        meta={"stage": "menu", "message": f"Building your digital menu…{retry_note}"},
    )
    menu = extract_menu(
        MenuExtractRequest(
            lines=[
                MenuExtractLine(
                    text=line.text,
                    confidence=line.confidence,
                    reading_order=line.reading_order,
                    bbox=line.bbox,
                )
                for line in ocr.lines
            ],
            full_text=ocr.full_text,
        )
    )
    return menu.model_dump(mode="json")
