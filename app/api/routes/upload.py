import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import (
    RATE_LIMIT_UPLOAD,
    RATE_LIMIT_WINDOW_SECONDS,
    UPLOAD_DIR,
)
from app.services.rate_limit import client_ip, enforce_rate_limit

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
) -> dict[str, str | int]:
    enforce_rate_limit(
        scope="upload",
        identity=client_ip(request),
        limit=RATE_LIMIT_UPLOAD,
        window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    original_name = Path(file.filename or "upload").name
    if not original_name or original_name in {".", ".."}:
        original_name = "upload"

    saved_name = f"{uuid.uuid4().hex}_{original_name}"
    destination = UPLOAD_DIR / saved_name

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    destination.write_bytes(contents)

    # Durable, browser-fetchable path (proxied via nginx / Vite in frontend).
    image_url = f"/uploads/{saved_name}"

    return {
        "filename": saved_name,
        "url": image_url,
        "file_size": len(contents),
        "content_type": file.content_type,
    }
