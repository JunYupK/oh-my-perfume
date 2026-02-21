from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings

_CLIENT = AsyncOpenAI(api_key=settings.openai_api_key)


def _build_perfume_text(payload: dict) -> str:
    brand = payload.get("brand", "")
    name = payload.get("name", "")
    year = payload.get("year")
    concentration = payload.get("concentration", "")
    gender = payload.get("gender", "")
    accords = ", ".join(payload.get("accords", []))
    top_notes = ", ".join(payload.get("top_notes", []))
    middle_notes = ", ".join(payload.get("middle_notes", []))
    base_notes = ", ".join(payload.get("base_notes", []))

    year_text = f" ({year})" if year else ""
    return (
        f"{brand} {name}{year_text}. {concentration}, {gender}. "
        f"향 계열: {accords}. 탑노트: {top_notes}. 미들노트: {middle_notes}. 베이스노트: {base_notes}."
    )


async def embed_text(text: str) -> list[float]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    response = await _CLIENT.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding
