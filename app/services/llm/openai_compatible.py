from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT_SECONDS
from app.services.llm.provider import (
    LLMConfigError,
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
)


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._api_key = (api_key if api_key is not None else LLM_API_KEY).strip()
        self._model = (model if model is not None else LLM_MODEL).strip()
        self._base_url = (base_url if base_url is not None else LLM_BASE_URL).rstrip("/")
        self._timeout = (
            timeout_seconds if timeout_seconds is not None else LLM_TIMEOUT_SECONDS
        )

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._api_key:
            raise LLMConfigError("LLM_API_KEY is not configured")
        if not self._model:
            raise LLMConfigError("LLM_MODEL is not configured")
        if not self._base_url:
            raise LLMConfigError("LLM_BASE_URL is not configured")

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "menu_extraction",
                    "strict": True,
                    "schema": response_schema,
                },
            },
            "temperature": 0,
        }

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"LLM request timed out after {self._timeout}s"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"LLM request failed: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text.strip() or response.reason_phrase
            raise LLMProviderError(
                f"LLM provider returned HTTP {response.status_code}: {detail}"
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError("LLM provider returned non-JSON response") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "LLM provider response missing message content"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("LLM provider returned empty message content")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LLM provider returned invalid JSON content") from exc

        if not isinstance(parsed, dict):
            raise LLMProviderError("LLM provider JSON root must be an object")

        return parsed
