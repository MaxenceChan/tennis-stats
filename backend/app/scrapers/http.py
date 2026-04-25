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
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


async def fetch(url: str, *, params: dict[str, Any] | None = None) -> str:
    await _throttle()
    headers = dict(_BROWSER_HEADERS)
    # Override UA only if user explicitly set a non-default value (non-bot)
    if _settings.user_agent and "bot" not in _settings.user_agent.lower():
        headers["User-Agent"] = _settings.user_agent
    async with httpx.AsyncClient(timeout=_settings.scrape_timeout_sec, follow_redirects=True) as client:
        logger.debug("GET %s params=%s", url, params)
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code >= 500:
            resp.raise_for_status()
        resp.raise_for_status()
        return resp.text
