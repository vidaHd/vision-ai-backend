from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from app.core.config import OCR_MAX_IMAGE_SIDE


def preprocess_image(source: Path, destination: Path) -> tuple[int, int]:
    """Fix EXIF orientation and downscale large images. Returns (width, height)."""
    with Image.open(source) as image:
        oriented = ImageOps.exif_transpose(image)
        rgb = oriented.convert("RGB")

        width, height = rgb.size
        longest = max(width, height)
        if longest > OCR_MAX_IMAGE_SIDE:
            scale = OCR_MAX_IMAGE_SIDE / longest
            width = max(1, int(width * scale))
            height = max(1, int(height * scale))
            rgb = rgb.resize((width, height), Image.Resampling.LANCZOS)

        destination.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(destination, format="JPEG", quality=92)
        return width, height
