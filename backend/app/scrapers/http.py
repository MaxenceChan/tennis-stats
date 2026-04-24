"""Client HTTP partagé avec backoff + rate-limit simple."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()

_last_request_at: float = 0.0
_lock = asyncio.Lock()


async def _throttle() -> None:
    global _last_request_at
    async with _lock:
        loop = asyncio.get_event_loop()
        now = loop.time()
        wait = _settings.scrape_delay_sec - (now - _last_request_at)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_at = loop.time()


@retry(
    reraise=True,
    stop=stop_after_attempt(_settings.scrape_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
)
async def fetch(url: str, *, params: dict[str, Any] | None = None) -> str:
    await _throttle()
    headers = {"User-Agent": _settings.user_agent, "Accept-Language": "en-US,en;q=0.9"}
    async with httpx.AsyncClient(timeout=_settings.scrape_timeout_sec, follow_redirects=True) as client:
        logger.debug("GET %s params=%s", url, params)
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code >= 500:
            resp.raise_for_status()
        resp.raise_for_status()
        return resp.text
