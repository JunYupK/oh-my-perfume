from __future__ import annotations

import argparse
import asyncio
import random
from datetime import datetime, timedelta, timezone
import re

import redis.asyncio as redis
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, MemoryAdaptiveDispatcher, RateLimiter
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models import Brand, CrawlStateLog, NoteType, Perfume, PerfumeAccord, PerfumeEmbedding, PerfumeNote
from crawler.embedder import _build_perfume_text, embed_text
from crawler.extractors import build_extraction_strategy
from crawler.state import clear_crawl_state, load_crawl_state, save_crawl_state
from crawler.strategies import build_brand_strategy

BRAND_URL_TEMPLATE = "https://www.fragrantica.com/designers/{brand}/"


ALLOWED_CONCENTRATIONS = {
    "edp": "EDP",
    "edt": "EDT",
    "parfum": "Parfum",
    "edc": "EDC",
    "edp intense": "EDP Intense",
}

ALLOWED_GENDERS = {
    "men": "Men",
    "women": "Women",
    "unisex": "Unisex",
}

UNSET_TEXT = "unknown"


def _slugify(value: str) -> str:
    normalized = value.lower().strip()
    normalized = normalized.replace("/", "-")
    normalized = re.sub(r"[\s_]+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def _normalize_text_value(value: object, mapping: dict[str, str], fallback: str = UNSET_TEXT) -> str:
    if not isinstance(value, str):
        return fallback

    normalized = value.strip().lower()
    if not normalized:
        return fallback

    if normalized in mapping:
        return mapping[normalized]

    return value.strip()


def _normalize_payload(payload: dict) -> dict:
    payload["concentration"] = _normalize_text_value(
        payload.get("concentration"), ALLOWED_CONCENTRATIONS, UNSET_TEXT
    )
    payload["gender"] = _normalize_text_value(payload.get("gender"), ALLOWED_GENDERS, UNSET_TEXT)
    payload["accords"] = _extract_list(payload, "accords")
    return payload


def _normalize_state_key(brand: str) -> str:
    return f"brand:{brand.lower()}"


def _note_entries(payload: dict, note_type: NoteType) -> list[PerfumeNote]:
    notes = payload.get(f"{note_type.value}_notes", [])
    if not isinstance(notes, list):
        return []
    return [
        PerfumeNote(note_name=note.strip(), note_type=note_type)
        for note in notes
        if isinstance(note, str) and note.strip()
    ]


def _extract_list(payload: dict, key: str) -> list[str]:
    raw = payload.get(key, [])
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


async def recently_crawled(db, url: str) -> bool:
    stmt = select(Perfume).where(Perfume.fragrantica_url == url)
    perfume = (await db.execute(stmt)).scalar_one_or_none()
    if not perfume or not perfume.last_crawled_at:
        return False
    now = datetime.now(timezone.utc)
    return perfume.last_crawled_at and perfume.last_crawled_at > now - timedelta(hours=24)


async def upsert_brand(session, payload: dict) -> Brand:
    brand_name = payload["brand"]
    stmt = select(Brand).where(Brand.slug == _slugify(brand_name))
    brand = (await session.execute(stmt)).scalar_one_or_none()
    if brand:
        return brand

    brand = Brand(
        name=brand_name,
        slug=_slugify(brand_name),
        fragrantica_url=BRAND_URL_TEMPLATE.format(brand=_slugify(brand_name)),
    )
    session.add(brand)
    await session.flush()
    return brand


async def upsert_perfume(session, payload, brand_obj: Brand) -> Perfume:
    slug = _slugify(payload.get("name", ""))
    stmt = select(Perfume).where(Perfume.brand_id == brand_obj.id, Perfume.slug == slug)
    perfume = (await session.execute(stmt)).scalar_one_or_none()

    if not perfume:
        perfume = Perfume(
            brand_id=brand_obj.id,
            name=payload["name"],
            slug=slug,
            fragrantica_url=payload["source_url"],
            year=payload.get("year"),
            concentration=payload.get("concentration", ""),
            gender=payload.get("gender", ""),
            last_crawled_at=datetime.now(timezone.utc),
        )
        session.add(perfume)
    else:
        perfume.name = payload["name"]
        perfume.year = payload.get("year")
        perfume.concentration = payload.get("concentration", "")
        perfume.gender = payload.get("gender", "")
        perfume.fragrantica_url = payload["source_url"]
        perfume.last_crawled_at = datetime.now(timezone.utc)

    await session.flush()
    return perfume


async def upsert_notes_and_accords(session, perfume: Perfume, payload: dict):
    await session.execute(delete(PerfumeNote).where(PerfumeNote.perfume_id == perfume.id))
    await session.execute(delete(PerfumeAccord).where(PerfumeAccord.perfume_id == perfume.id))

    notes = _note_entries(payload, NoteType.top) + _note_entries(payload, NoteType.middle) + _note_entries(
        payload, NoteType.base
    )
    for entry in notes:
        entry.perfume = perfume
        session.add(entry)

    for accord_name in _extract_list(payload, "accords"):
        session.add(
            PerfumeAccord(perfume_id=perfume.id, accord_name=accord_name, strength=1.0)
        )


async def embed_and_store(session, perfume: Perfume, payload: dict):
    text = _build_perfume_text(payload)
    vector = await embed_text(text)

    await session.execute(delete(PerfumeEmbedding).where(PerfumeEmbedding.perfume_id == perfume.id))
    session.add(PerfumeEmbedding(perfume_id=perfume.id, embedding=vector))


async def process_result(result, session, db):
    if "/perfume/" not in result.url:
        return

    payload = result.extracted_content
    if not isinstance(payload, dict):
        try:
            payload = payload.dict()
        except Exception:
            return
    if not payload:
        return

    if "name" not in payload or "brand" not in payload:
        return

    payload = _normalize_payload(payload)
    if await recently_crawled(db, result.url):
        return

    payload["source_url"] = result.url
    brand_obj = await upsert_brand(session, payload)
    perfume = await upsert_perfume(session, payload, brand_obj)
    await upsert_notes_and_accords(session, perfume, payload)
    await embed_and_store(session, perfume, payload)
    await session.flush()


async def crawl_brand(brand: str, crawler, session, max_pages: int | None = None):
    session_key = _normalize_state_key(brand)
    redis_client = redis.from_url(settings.redis_url)
    resume_state = await load_crawl_state(redis_client, session_key)
    crawl_state = {}

    async def on_state_change(state):
        if isinstance(state, dict):
            crawl_state.update(
                {
                    "total_pages": state.get("total_pages"),
                    "processed_pages": state.get("processed_pages"),
                }
            )
        await save_crawl_state(redis_client, session_key, state)

    strategy = build_brand_strategy(
        on_state_change=on_state_change,
        resume_state=resume_state,
        max_pages=max_pages or settings.crawler_max_pages_per_brand,
    )

    crawl_log = CrawlStateLog(
        session_key=session_key,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(crawl_log)
    await session.flush()

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        extraction_strategy=build_extraction_strategy(),
        prefetch=True,
        streaming=True,
        dispatcher=MemoryAdaptiveDispatcher(
            memory_threshold_percent=70.0,
            rate_limiter=RateLimiter(
                base_delay=(3.0, 5.0),
                max_retries=5,
                rate_limit_codes=[429, 503],
            ),
        ),
    )

    url = BRAND_URL_TEMPLATE.format(brand=brand)
    try:
        results = await crawler.arun(url=url, config=run_config)
        if hasattr(results, "__aiter__"):
            async for result in results:
                await process_result(result, session, session)
        else:
            for result in results:
                await process_result(result, session, session)

        crawl_log.status = "completed"
        crawl_log.finished_at = datetime.now(timezone.utc)
    except Exception as exc:
        crawl_log.status = "failed"
        crawl_log.finished_at = datetime.now(timezone.utc)
        await session.flush()
        await clear_crawl_state(redis_client, session_key)
        raise
    finally:
        crawl_state_payload = await load_crawl_state(redis_client, session_key) or {}
        if not crawl_state:
            crawl_state = crawl_state_payload
        crawl_log.total_pages = crawl_state.get("total_pages")
        crawl_log.processed_pages = crawl_state.get("processed_pages")
        await session.flush()
        await clear_crawl_state(redis_client, session_key)
        await redis_client.aclose()


async def run_once(brands: list[str] | None = None, max_pages: int | None = None):
    brands_to_crawl = brands or settings.crawler_target_brands_list
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with AsyncWebCrawler() as crawler:
        for brand in brands_to_crawl:
            async with session_factory() as session:
                try:
                    await crawl_brand(brand, crawler, session, max_pages=max_pages)
                    await session.commit()
                    print(f"[{brand}] 완료")
                except Exception as e:
                    await session.rollback()
                    print(f"[{brand}] 실패: {e}")
            await asyncio.sleep(random.uniform(5, 10))


async def run():
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with AsyncWebCrawler() as crawler:
        while True:
            print("[Sillage] 새 크롤링 사이클 시작")
            for brand in settings.crawler_target_brands_list:
                async with session_factory() as session:
                    try:
                        await crawl_brand(brand, crawler, session)
                        await session.commit()
                        print(f"[{brand}] 완료")
                    except Exception as e:
                        await session.rollback()
                        print(f"[{brand}] 실패: {e}")

                await asyncio.sleep(random.uniform(5, 10))

            print("[Sillage] 사이클 완료. 24시간 대기 후 재시작")
            await asyncio.sleep(60 * 60 * 24)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fragrantica perfume crawler")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument(
        "--brand",
        action="append",
        help="Run only the selected brand. Can be used multiple times",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Override max pages per brand",
    )

    args = parser.parse_args()

    if args.once:
        selected_brands = args.brand
        asyncio.run(run_once(brands=selected_brands, max_pages=args.max_pages))
    else:
        asyncio.run(run())
