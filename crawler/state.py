from __future__ import annotations

import json


STATE_KEY_PREFIX = "crawl:state:"


def _state_key(session_key: str) -> str:
    return f"{STATE_KEY_PREFIX}{session_key}"


async def save_crawl_state(redis_client, session_key: str, state: dict) -> None:
    await redis_client.set(_state_key(session_key), json.dumps(state))


async def load_crawl_state(redis_client, session_key: str) -> dict | None:
    raw = await redis_client.get(_state_key(session_key))
    if not raw:
        return None

    payload = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
    return json.loads(payload)


async def clear_crawl_state(redis_client, session_key: str) -> None:
    await redis_client.delete(_state_key(session_key))
