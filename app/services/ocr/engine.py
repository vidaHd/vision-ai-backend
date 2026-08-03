from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawLine:
    text: str
    confidence: float
    bbox: list[list[float]]


class OCREngine(ABC):
    name: str

    @abstractmethod
    def run(self, image_path: Path) -> list[RawLine]:
        """Extract text lines with bounding boxes from an image."""
