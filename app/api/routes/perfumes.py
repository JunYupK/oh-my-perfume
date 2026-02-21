from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession
from app.models.perfume import Perfume
from app.schemas.perfume import PerfumeDetailSchema, PerfumeSearchRequest, PerfumeSearchResult
from rag.retriever import search_perfumes

router = APIRouter(prefix="/api/perfumes", tags=["perfumes"])


@router.post("/search", response_model=list[PerfumeSearchResult])
async def search(payload: PerfumeSearchRequest, db: DBSession):
    try:
        return await search_perfumes(payload.query, payload.limit, db)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/trending", response_model=list[PerfumeDetailSchema])
async def trending(db: DBSession, limit: int = 10):
    if limit < 1:
        limit = 10
    if limit > 50:
        limit = 50

    stmt = (
        select(Perfume)
        .options(selectinload(Perfume.brand), selectinload(Perfume.notes), selectinload(Perfume.accords))
        .order_by(desc(Perfume.last_crawled_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()


@router.get("/{slug}", response_model=PerfumeDetailSchema)
async def get_perfume(slug: str, db: DBSession):
    stmt = (
        select(Perfume)
        .where(Perfume.slug == slug)
        .options(
            selectinload(Perfume.brand),
            selectinload(Perfume.notes),
            selectinload(Perfume.accords),
        )
    )
    result = await db.execute(stmt)
    perfume = result.scalars().unique().one_or_none()
    if not perfume:
        raise HTTPException(status_code=404, detail="Perfume not found")
    return perfume
