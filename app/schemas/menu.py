from __future__ import annotations

from pydantic import BaseModel, Field


class MenuExtractLine(BaseModel):
    text: str
    confidence: float
    reading_order: int
    bbox: list[list[float]] = Field(default_factory=list)


class MenuExtractRequest(BaseModel):
    lines: list[MenuExtractLine] = Field(..., min_length=1)
    full_text: str = ""


class MenuItem(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None
    currency: str | None = None


class MenuCategory(BaseModel):
    name: str
    items: list[MenuItem] = Field(default_factory=list)


class MenuLlmOutput(BaseModel):
    """Strict schema for validating raw LLM JSON before building the API response."""

    categories: list[MenuCategory] = Field(default_factory=list)
    currency: str | None = None
    warnings: list[str] = Field(default_factory=list)


class OcrEcho(BaseModel):
    lines: list[MenuExtractLine]
    full_text: str


class MenuExtractResponse(BaseModel):
    categories: list[MenuCategory]
    currency: str | None = None
    ocr: OcrEcho
    warnings: list[str] = Field(default_factory=list)
