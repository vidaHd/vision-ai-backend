from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMConfigError(Exception):
    """Provider is missing required configuration (e.g. API key)."""


class LLMTimeoutError(Exception):
    """Provider request exceeded the configured timeout."""


class LLMProviderError(Exception):
    """Upstream provider or network failure."""


class LLMResponseValidationError(Exception):
    """Provider returned JSON that failed schema validation."""


class LLMProvider(ABC):
    @abstractmethod
    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a parsed JSON object. Raises typed provider errors on failure."""
