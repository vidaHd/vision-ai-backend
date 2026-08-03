from __future__ import annotations

from typing import Any

from app.schemas.menu import (
    MenuExtractLine,
    MenuExtractRequest,
    MenuExtractResponse,
    OcrEcho,
)
from app.services.menu.service import extract_menu
from app.services.ocr.service import run_ocr
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="extract_menu_pipeline")
def extract_menu_pipeline(self, filename: str) -> dict[str, Any]:
    """Run OCR then LLM menu structuring; report progress via Celery state."""
    self.update_state(
        state="PROGRESS",
        meta={"stage": "ocr", "message": "Reading the menu…"},
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
        meta={"stage": "menu", "message": "Building your digital menu…"},
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
