from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas.menu import (
    MenuExtractRequest,
    MenuExtractResponse,
    MenuLlmOutput,
    OcrEcho,
)
from app.services.llm.factory import get_llm_provider
from app.services.llm.provider import LLMProvider, LLMResponseValidationError
from app.services.menu.prompts import SYSTEM_PROMPT, build_user_prompt


def _llm_response_schema() -> dict[str, Any]:
    """JSON Schema for structured outputs (OpenAI strict mode compatible)."""
    schema = MenuLlmOutput.model_json_schema()
    return _make_strict_schema(schema)


def _make_strict_schema(node: Any) -> Any:
    """Require all properties and disallow extras (OpenAI strict json_schema)."""
    if isinstance(node, dict):
        updated = {
            key: _make_strict_schema(value) for key, value in node.items()
        }
        if updated.get("type") == "object" or "properties" in updated:
            props = updated.get("properties")
            if isinstance(props, dict):
                updated["required"] = list(props.keys())
            updated["additionalProperties"] = False
        return updated
    if isinstance(node, list):
        return [_make_strict_schema(item) for item in node]
    return node


def extract_menu(
    request: MenuExtractRequest,
    *,
    provider: LLMProvider | None = None,
) -> MenuExtractResponse:
    llm = provider or get_llm_provider()
    user_prompt = build_user_prompt(request.lines, request.full_text)

    raw = llm.complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_schema=_llm_response_schema(),
    )

    try:
        parsed = MenuLlmOutput.model_validate(raw)
    except ValidationError as exc:
        raise LLMResponseValidationError(
            f"LLM response failed validation: {exc}"
        ) from exc

    return MenuExtractResponse(
        categories=parsed.categories,
        currency=parsed.currency,
        ocr=OcrEcho(lines=list(request.lines), full_text=request.full_text),
        warnings=list(parsed.warnings),
    )
