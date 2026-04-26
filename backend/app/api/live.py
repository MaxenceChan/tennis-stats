"""Endpoints live (matches en cours + classement live) — passthrough RapidAPI.

Cache 60 s en mémoire pour économiser le quota (60 req/mois sur Basic free).
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException

from app.scrapers import tennisapi1

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/live", tags=["live"])

CACHE_TTL = 60.0  # seconds
_cache: dict[str, tuple[float, Any]] = {}
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(key: str) -> asyncio.Lock:
    lock = _locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _locks[key] = lock
    return lock


async def _cached(key: str, fetch):
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    async with _get_lock(key):
        # double-check after lock
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < CACHE_TTL:
            return hit[1]
        try:
            value = await fetch()
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        except Exception as exc:
            logger.exception("live fetch failed for %s", key)
            # if we have stale data, return it rather than 502
            if hit:
                logger.warning("returning stale cache for %s after error", key)
                return hit[1]
            raise HTTPException(502, f"upstream error: {type(exc).__name__}") from exc
        _cache[key] = (time.monotonic(), value)
        return value


@router.get("/rankings")
async def live_rankings(limit: int = 100):
    rows = await _cached("rankings", tennisapi1.fetch_live_rankings)
    return [asdict(r) for r in rows[:limit]]


@router.get("/matches")
async def live_matches():
    rows = await _cached("matches", tennisapi1.fetch_live_matches)
    return [asdict(r) for r in rows]
