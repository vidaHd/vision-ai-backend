from __future__ import annotations

import os
import platform
from pathlib import Path
from threading import Lock

from app.core.config import OCR_LANG, OCR_MIN_CONFIDENCE
from app.services.ocr.engine import OCREngine, RawLine

# Skip paddlex hoster connectivity probe on every process start.
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# Native Paddle inference can SIGSEGV on Linux ARM64 (Docker on Apple Silicon).
_IS_ARM64 = platform.machine().lower() in {"aarch64", "arm64"}
if _IS_ARM64:
    os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
    os.environ.setdefault("FLAGS_enable_pir_api", "0")
    os.environ.setdefault("FLAGS_use_mkldnn", "0")


class PaddleOCREngine(OCREngine):
    name = "paddleocr"

    def __init__(self) -> None:
        self._ocr = None
        self._lock = Lock()

    def _get_ocr(self):
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    from paddleocr import PaddleOCR

                    init_kwargs: dict = {
                        "lang": OCR_LANG,
                        "use_doc_orientation_classify": False,
                        "use_doc_unwarping": False,
                        "use_textline_orientation": False,
                        "enable_mkldnn": False,
                    }
                    if _IS_ARM64:
                        # Bypass broken native kernels via ONNX Runtime.
                        init_kwargs["engine"] = "onnxruntime"

                    self._ocr = PaddleOCR(**init_kwargs)
        return self._ocr

    def run(self, image_path: Path) -> list[RawLine]:
        results = self._get_ocr().predict(str(image_path))
        if not results:
            return []

        page = results[0]
        texts = list(page.get("rec_texts") or [])
        scores = list(page.get("rec_scores") or [])
        polys = list(page.get("rec_polys") or page.get("dt_polys") or [])

        lines: list[RawLine] = []
        for index, text in enumerate(texts):
            confidence = float(scores[index]) if index < len(scores) else 0.0
            if confidence < OCR_MIN_CONFIDENCE:
                continue

            cleaned = str(text).strip()
            if not cleaned:
                continue

            bbox: list[list[float]] = []
            if index < len(polys):
                poly = polys[index]
                bbox = [[float(x), float(y)] for x, y in poly]

            lines.append(
                RawLine(text=cleaned, confidence=confidence, bbox=bbox),
            )

        return lines


_engine: PaddleOCREngine | None = None
_engine_lock = Lock()


def get_paddle_engine() -> PaddleOCREngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = PaddleOCREngine()
    return _engine
