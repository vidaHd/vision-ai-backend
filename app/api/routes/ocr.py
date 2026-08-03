import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas.ocr import OcrRequest, OcrResponse
from app.services.ocr.service import run_ocr

router = APIRouter(tags=["ocr"])


@router.post("/ocr", response_model=OcrResponse)
async def extract_text(body: OcrRequest) -> OcrResponse:
    try:
        return await asyncio.to_thread(run_ocr, body.filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {exc}",
        ) from exc
