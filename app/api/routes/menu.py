from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas.menu import MenuExtractRequest, MenuExtractResponse
from app.services.llm.provider import (
    LLMConfigError,
    LLMProviderError,
    LLMResponseValidationError,
    LLMTimeoutError,
)
from app.services.menu.service import extract_menu

router = APIRouter(tags=["menu"])


@router.post("/menu/extract", response_model=MenuExtractResponse)
async def extract_menu_endpoint(body: MenuExtractRequest) -> MenuExtractResponse:
    try:
        return await asyncio.to_thread(extract_menu, body)
    except LLMConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except LLMResponseValidationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Menu extraction failed: {exc}",
        ) from exc
