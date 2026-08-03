from pydantic import BaseModel, Field


class OcrRequest(BaseModel):
    filename: str = Field(..., min_length=1)


class PageSize(BaseModel):
    width: int
    height: int


class OcrLine(BaseModel):
    text: str
    confidence: float
    bbox: list[list[float]]
    reading_order: int


class OcrResponse(BaseModel):
    filename: str
    engine: str
    page: PageSize
    lines: list[OcrLine]
    full_text: str
