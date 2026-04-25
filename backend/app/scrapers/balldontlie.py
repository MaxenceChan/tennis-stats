"""
Scraper BallDontLie ATP API (free tier).

Free tier endpoints (5 requests / minute, key required):
  GET /atp/v1/players       — bios (id, name, country, height, weight, plays)
  GET /atp/v1/tournaments   — calendar (name, location, surface, category, dates)
  GET /atp/v1/rankings      — current ATP rankings (player + rank + points)

NOT in free tier (paid ALL-STAR $9.99/mo):
  /atp/v1/matches  → winner / loser / score / round  ❌

Auth : header `Authorization: <api_key>` (no "Bearer " prefix).
Pagination : cursor-based (`?cursor=<next_cursor>`), per_page max 100.

Rate-limited : we sleep 13 s between calls (1 / 12 s + safety margin).
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.balldontlie.io/atp/v1"
THROTTLE_SECONDS = 13.0   # 5 req/min = 1 every 12 s; 13 = safety margin


@dataclass
class BdlPlayer:
    bdl_id: int
    full_name: str
    first_name: str | None
    last_name: str | None
    country: str | None        # 3-letter code if we can guess, else None
    country_name: str | None
    birth_place: str | None
    age: int | None
    height_cm: int | None
    weight_kg: int | None
    plays: str | None          # "Right-Handed" / "Left-Handed"
    turned_pro: int | None


@dataclass
class BdlTournament:
    bdl_id: int
    name: str
    location: str | None
    surface: str | None
    category: str | None       # ATP 250 / ATP 500 / Masters 1000 / Grand Slam
    season: int
    start_date: date | None
    end_date: date | None
    prize_money: int | None
    prize_currency: str | None
    draw_size: int | None


@dataclass
class BdlRanking:
    player_bdl_id: int
    full_name: str
    rank: int
    points: int | None
    movement: int | None
    ranking_date: date | None


def _api_key() -> str:
    key = os.environ.get("BDL_API_KEY", "").strip()
    if not key:
        raise RuntimeError("BDL_API_KEY env var missing")
    return key


def _hand_letter(plays: str | None) -> str | None:
    if not plays:
        return None
    p = plays.lower()
    if "left" in p:
        return "L"
    if "right" in p:
        return "R"
    return None


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


async def _get_paginated(client: httpx.AsyncClient, path: str,
                         params: dict | None = None,
                         max_pages: int = 50) -> list[dict]:
    """Iterate cursor-paginated endpoint, throttling to stay under 5 req/min."""
    headers = {"Authorization": _api_key()}
    out: list[dict] = []
    cursor: int | None = None
    for page in range(max_pages):
        q = dict(params or {})
        q["per_page"] = 100
        if cursor is not None:
            q["cursor"] = cursor
        url = f"{BASE_URL}{path}"
        logger.info("GET %s page=%d cursor=%s", url, page + 1, cursor)
        r = await client.get(url, params=q, headers=headers, timeout=30.0)
        if r.status_code == 429:
            logger.warning("rate-limited, sleeping 30 s and retrying")
            await asyncio.sleep(30.0)
            r = await client.get(url, params=q, headers=headers, timeout=30.0)
        r.raise_for_status()
        body = r.json()
        out.extend(body.get("data", []))
        cursor = (body.get("meta") or {}).get("next_cursor")
        if cursor is None:
            break
        await asyncio.sleep(THROTTLE_SECONDS)
    return out


# ---------------------------------------------------------------- public API

async def fetch_rankings() -> list[BdlRanking]:
    async with httpx.AsyncClient() as client:
        rows = await _get_paginated(client, "/rankings")
    out = []
    for row in rows:
        p = row.get("player") or {}
        out.append(BdlRanking(
            player_bdl_id=p.get("id"),
            full_name=p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
            rank=row.get("rank"),
            points=row.get("points"),
            movement=row.get("movement"),
            ranking_date=_parse_date(row.get("ranking_date")),
        ))
    return out


async def fetch_players(max_pages: int = 20) -> list[BdlPlayer]:
    async with httpx.AsyncClient() as client:
        rows = await _get_paginated(client, "/players", max_pages=max_pages)
    return [
        BdlPlayer(
            bdl_id=r.get("id"),
            full_name=r.get("full_name") or f"{r.get('first_name','')} {r.get('last_name','')}".strip(),
            first_name=r.get("first_name"),
            last_name=r.get("last_name"),
            country=(r.get("country_code") or "")[:3] or None,
            country_name=r.get("country"),
            birth_place=r.get("birth_place"),
            age=r.get("age"),
            height_cm=r.get("height_cm"),
            weight_kg=r.get("weight_kg"),
            plays=r.get("plays"),
            turned_pro=r.get("turned_pro"),
        )
        for r in rows
    ]


async def fetch_tournaments(season: int | None = None,
                            max_pages: int = 10) -> list[BdlTournament]:
    params = {"season": season} if season else None
    async with httpx.AsyncClient() as client:
        rows = await _get_paginated(client, "/tournaments", params=params,
                                    max_pages=max_pages)
    return [
        BdlTournament(
            bdl_id=r.get("id"),
            name=r.get("name") or "",
            location=r.get("location"),
            surface=r.get("surface"),
            category=r.get("category"),
            season=r.get("season"),
            start_date=_parse_date(r.get("start_date")),
            end_date=_parse_date(r.get("end_date")),
            prize_money=r.get("prize_money"),
            prize_currency=r.get("prize_currency"),
            draw_size=r.get("draw_size"),
        )
        for r in rows
    ]
