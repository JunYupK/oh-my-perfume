from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class PerfumeExtractSchema(BaseModel):
    name: str
    brand: str
    year: Optional[int] = None
    concentration: str
    gender: str
    accords: list[str]
    top_notes: list[str]
    middle_notes: list[str]
    base_notes: list[str]
