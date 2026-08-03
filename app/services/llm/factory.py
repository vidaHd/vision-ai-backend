from __future__ import annotations

from app.core.config import LLM_PROVIDER
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.llm.provider import LLMConfigError, LLMProvider


def get_llm_provider() -> LLMProvider:
    provider_id = (LLM_PROVIDER or "").strip().lower()
    if provider_id == "openai_compatible":
        return OpenAICompatibleProvider()
    raise LLMConfigError(f"Unsupported LLM provider: {LLM_PROVIDER!r}")
