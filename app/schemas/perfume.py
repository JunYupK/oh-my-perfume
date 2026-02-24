from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BrandSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    fragrantica_url: str


class NoteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_name: str
    note_type: str


class AccordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    accord_name: str
    strength: float


class PerfumeListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    year: int | None
    concentration: str
    gender: str
    fragrantica_url: str
    last_crawled_at: datetime | None


class PerfumeDetailSchema(PerfumeListSchema):
    brand: BrandSchema
    notes: list[NoteSchema]
    accords: list[AccordSchema]


class PerfumeSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)


class PerfumeSearchResult(BaseModel):
    perfume_id: int
    name: str
    brand_name: str
    url: str
    similarity: float
    year: int | None = None
    concentration: str
    gender: str
