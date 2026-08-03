from __future__ import annotations

import tempfile
from pathlib import Path

from app.core.config import OCR_ENGINE, UPLOAD_DIR
from app.schemas.ocr import OcrLine, OcrResponse, PageSize
from app.services.ocr.engine import OCREngine, RawLine
from app.services.ocr.paddle_engine import get_paddle_engine
from app.services.ocr.preprocess import preprocess_image


def resolve_upload_path(filename: str) -> Path:
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."} or safe_name != filename:
        raise ValueError("Invalid filename")

    path = (UPLOAD_DIR / safe_name).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if not path.is_relative_to(upload_root):
        raise ValueError("Invalid filename")
    if not path.is_file():
        raise FileNotFoundError(f"Uploaded file not found: {safe_name}")
    return path


def get_engine() -> OCREngine:
    if OCR_ENGINE == "paddleocr":
        return get_paddle_engine()
    raise ValueError(f"Unsupported OCR engine: {OCR_ENGINE}")


def _sort_key(line: RawLine) -> tuple[float, float]:
    if not line.bbox:
        return (0.0, 0.0)
    ys = [point[1] for point in line.bbox]
    xs = [point[0] for point in line.bbox]
    # Band Y so same-row name/price pairs sort left-to-right.
    y_band = round(min(ys) / 20.0) * 20.0
    return (y_band, min(xs))


def normalize_lines(raw_lines: list[RawLine]) -> list[OcrLine]:
    ordered = sorted(raw_lines, key=_sort_key)
    return [
        OcrLine(
            text=line.text,
            confidence=round(line.confidence, 4),
            bbox=line.bbox,
            reading_order=index,
        )
        for index, line in enumerate(ordered)
    ]


def run_ocr(filename: str) -> OcrResponse:
    source = resolve_upload_path(filename)
    engine = get_engine()

    with tempfile.TemporaryDirectory(prefix="ocr_") as tmp:
        prepared = Path(tmp) / "prepared.jpg"
        width, height = preprocess_image(source, prepared)
        raw_lines = engine.run(prepared)

    lines = normalize_lines(raw_lines)
    return OcrResponse(
        filename=source.name,
        engine=engine.name,
        page=PageSize(width=width, height=height),
        lines=lines,
        full_text="\n".join(line.text for line in lines),
    )
