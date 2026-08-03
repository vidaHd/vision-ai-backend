from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load shared project .env, then optional backend/.env for missing keys only.
# Existing OS env (e.g. Docker Compose) always wins — never override it.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_ROOT.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_BACKEND_ROOT / ".env")

APP_NAME = "Vision AI Extractor API"
APP_VERSION = "0.1.0"
DEBUG = False
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

# OCR
OCR_ENGINE = "paddleocr"
OCR_LANG = "en"
OCR_USE_GPU = False
OCR_MIN_CONFIDENCE = 0.5
OCR_MAX_IMAGE_SIDE = 2500

# LLM (all secrets and provider settings from environment only)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai_compatible").strip() or "openai_compatible"
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL", "").strip() or "https://api.openai.com/v1"
)
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30") or "30")

# Database (required — set via environment / .env, never hardcode credentials)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to your environment or .env file "
        "(see .env.example)."
    )

# Auth / JWT
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Add it to your environment or .env file "
        "(see .env.example)."
    )
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60") or "60"
)

