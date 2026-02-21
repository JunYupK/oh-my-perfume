from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BrandSchema(BaseModel):
    id: int
    name: str
    slug: str
    fragrantica_url: str

    class Config:
        from_attributes = True


class NoteSchema(BaseModel):
    note_name: str
    note_type: str

    class Config:
        from_attributes = True


class AccordSchema(BaseModel):
    accord_name: str
    strength: float

    class Config:
        from_attributes = True


class PerfumeListSchema(BaseModel):
    id: int
    name: str
    slug: str
    year: int | None
    concentration: str
    gender: str
    fragrantica_url: str
    last_crawled_at: datetime | None

    class Config:
        from_attributes = True


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
