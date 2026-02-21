from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.models.brand import Brand
from app.models.perfume import Perfume
from app.schemas.perfume import BrandSchema, PerfumeListSchema

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("", response_model=list[BrandSchema])
async def list_brands(db: DBSession):
    result = await db.execute(select(Brand).order_by(Brand.name.asc()))
    return result.scalars().all()


@router.get("/{slug}/perfumes", response_model=list[PerfumeListSchema])
async def list_brand_perfumes(
    slug: str,
    db: DBSession,
    limit: int = Query(default=200, ge=1, le=500),
):
    brand_id = (await db.execute(select(Brand.id).where(Brand.slug == slug))).scalar_one_or_none()
    if brand_id is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    stmt = (
        select(Perfume)
        .where(Perfume.brand_id == brand_id)
        .order_by(Perfume.name.asc())
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()
