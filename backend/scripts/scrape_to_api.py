"""
Scrape côté GH Actions runner (IP Azure, peu blacklistée) puis POST vers l'API.

Modes :
  python -m scripts.scrape_to_api rankings           # top 1000 ATP/Race -> /import/rankings
  python -m scripts.scrape_to_api calendar           # tournois ATP -> /import/calendar
  python -m scripts.scrape_to_api bios --limit 50    # bios Wikipedia top N -> /import/player-bio
  python -m scripts.scrape_to_api matches --limit 50 # matches Tennis Abstract top N -> /import/player-matches
  python -m scripts.scrape_to_api full --limit 50    # rankings + calendar + bios + matches

Variables d'env requises :
  API_URL       ex: https://tennis-stats-api-tz1h.onrender.com
  ADMIN_TOKEN   bearer token (récupéré sur Render)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from dataclasses import asdict
from datetime import date

import httpx

from app.scrapers import atp_calendar, live_tennis, tennis_abstract, wikipedia
from app.scrapers.live_tennis import slugify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("scrape_to_api")


def _api_base() -> str:
    base = os.environ.get("API_URL", "").rstrip("/")
    if not base:
        log.error("API_URL env var is missing")
        sys.exit(2)
    return base


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("ADMIN_TOKEN", "")
    if not token:
        log.error("ADMIN_TOKEN env var is missing")
        sys.exit(2)
    return {"Authorization": f"Bearer {token}"}


def _serialize(obj):
    """JSON encoder helper for dates."""
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def post_json(client: httpx.AsyncClient, path: str, payload: dict) -> dict:
    url = f"{_api_base()}{path}"
    r = await client.post(
        url,
        json=payload,
        headers=_auth_headers(),
        timeout=httpx.Timeout(60.0, connect=15.0),
    )
    if r.status_code >= 400:
        log.error("POST %s -> %d : %s", path, r.status_code, r.text[:300])
        r.raise_for_status()
    return r.json()


async def get_json(client: httpx.AsyncClient, path: str) -> list | dict:
    url = f"{_api_base()}{path}"
    r = await client.get(
        url,
        headers=_auth_headers(),
        timeout=httpx.Timeout(30.0, connect=15.0),
    )
    r.raise_for_status()
    return r.json()


# ---------------------------- Rankings -----------------------------------------

async def push_rankings(client: httpx.AsyncClient, limit: int = 1000) -> None:
    log.info("Scraping ATP Live ranking (limit=%d)...", limit)
    atp = await live_tennis.fetch_atp_live(limit)
    log.info("  -> got %d ATP rows", len(atp))
    log.info("Scraping ATP Race ranking (limit=%d)...", limit)
    race = await live_tennis.fetch_atp_race(limit)
    log.info("  -> got %d Race rows", len(race))

    payload = {
        "atp": [
            {"rank": r.rank, "player_name": r.player_name,
             "country": r.country, "points": r.points}
            for r in atp
        ],
        "race": [
            {"rank": r.rank, "player_name": r.player_name,
             "country": r.country, "points": r.points}
            for r in race
        ],
    }
    log.info("POST /api/admin/import/rankings ...")
    res = await post_json(client, "/api/admin/import/rankings", payload)
    log.info("  -> ingested=%s", res.get("ingested"))


# ---------------------------- Calendar -----------------------------------------

async def push_calendar(client: httpx.AsyncClient) -> None:
    log.info("Scraping ATP calendar...")
    entries = await atp_calendar.fetch_calendar()
    log.info("  -> got %d entries", len(entries))
    payload = {
        "entries": [
            {
                "name": e.name, "slug": e.slug, "city": e.city,
                "country": e.country, "surface": e.surface,
                "category": e.category,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
            }
            for e in entries
        ]
    }
    log.info("POST /api/admin/import/calendar ...")
    res = await post_json(client, "/api/admin/import/calendar", payload)
    log.info("  -> ingested=%s", res.get("ingested"))


# ---------------------------- Bios (Wikipedia) ---------------------------------

async def push_bios(client: httpx.AsyncClient, limit: int = 50) -> None:
    log.info("Fetching player list (missing bio, limit=%d)...", limit)
    players = await get_json(client, f"/api/admin/players-list?limit={limit}&missing=bio")
    log.info("  -> %d players to enrich", len(players))
    for i, p in enumerate(players, 1):
        full_name = p["full_name"]
        slug = p["slug"]
        try:
            bio = await wikipedia.fetch_player_bio(full_name)
        except Exception as exc:  # noqa: BLE001
            log.warning("  [%d/%d] %s: wiki failed (%s)", i, len(players), full_name, exc)
            continue
        if not (bio.url or bio.birth_date or bio.height_cm):
            log.info("  [%d/%d] %s: no bio found", i, len(players), full_name)
            continue
        payload = {
            "full_name": full_name,
            "slug": slug,
            "wikipedia_url": bio.url,
            "birth_date": bio.birth_date.isoformat() if bio.birth_date else None,
            "height_cm": bio.height_cm,
            "weight_kg": bio.weight_kg,
            "hand": bio.hand,
            "backhand": bio.backhand,
        }
        try:
            await post_json(client, "/api/admin/import/player-bio", payload)
            log.info("  [%d/%d] %s: bio pushed", i, len(players), full_name)
        except Exception as exc:  # noqa: BLE001
            log.warning("  [%d/%d] %s: POST failed (%s)", i, len(players), full_name, exc)


# ---------------------------- Matches (Tennis Abstract) ------------------------

async def push_matches(client: httpx.AsyncClient, limit: int = 50) -> None:
    log.info("Fetching player list (missing matches, limit=%d)...", limit)
    players = await get_json(client, f"/api/admin/players-list?limit={limit}&missing=matches")
    log.info("  -> %d players to scrape on Tennis Abstract", len(players))
    for i, p in enumerate(players, 1):
        full_name = p["full_name"]
        slug = p["slug"]
        ta_slug = tennis_abstract.player_slug_for_url(full_name)
        url = f"{tennis_abstract.PLAYER_URL}?p={ta_slug}"
        try:
            profile = await tennis_abstract.fetch_player_profile(ta_slug)
        except Exception as exc:  # noqa: BLE001
            log.warning("  [%d/%d] %s: TA failed (%s)", i, len(players), full_name, exc)
            continue
        if not profile.matches:
            log.info("  [%d/%d] %s: no matches found", i, len(players), full_name)
            # Mark as scraped anyway by sending the URL — avoid re-scraping forever
            await post_json(client, "/api/admin/import/player-matches", {
                "owner_full_name": full_name,
                "owner_slug": slug,
                "tennis_abstract_url": url,
                "matches": [],
            })
            continue
        payload = {
            "owner_full_name": full_name,
            "owner_slug": slug,
            "tennis_abstract_url": url,
            "matches": [
                {
                    "match_date": sm.match_date.isoformat() if sm.match_date else None,
                    "tournament_name": sm.tournament_name,
                    "surface": sm.surface,
                    "round": sm.round,
                    "opponent_name": sm.opponent_name,
                    "opponent_rank": sm.opponent_rank,
                    "own_rank": sm.own_rank,
                    "result": sm.result,
                    "score": sm.score,
                    "sets_count": sm.sets_count,
                    "duration_minutes": sm.duration_minutes,
                    "stats": sm.stats,
                    "source_url": sm.source_url,
                }
                for sm in profile.matches
            ],
        }
        try:
            res = await post_json(client, "/api/admin/import/player-matches", payload)
            log.info("  [%d/%d] %s: %d matches pushed", i, len(players),
                     full_name, res.get("ingested", 0))
        except Exception as exc:  # noqa: BLE001
            log.warning("  [%d/%d] %s: POST failed (%s)", i, len(players), full_name, exc)


# ---------------------------- Elo recompute ------------------------------------

async def trigger_elo_recompute(client: httpx.AsyncClient) -> None:
    log.info("POST /api/admin/elo/recompute ...")
    url = f"{_api_base()}/api/admin/elo/recompute"
    r = await client.post(url, headers=_auth_headers(),
                          timeout=httpx.Timeout(120.0, connect=15.0))
    r.raise_for_status()
    log.info("  -> %s", r.json())


# ---------------------------- CLI ---------------------------------------------

async def amain() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["rankings", "calendar", "bios", "matches",
                                         "elo", "full"])
    parser.add_argument("--limit", type=int, default=50,
                        help="Number of players to enrich (bios/matches)")
    parser.add_argument("--rankings-limit", type=int, default=1000,
                        help="Max rank to import")
    args = parser.parse_args()

    async with httpx.AsyncClient() as client:
        if args.mode in ("rankings", "full"):
            await push_rankings(client, limit=args.rankings_limit)
        if args.mode in ("calendar", "full"):
            try:
                await push_calendar(client)
            except Exception as exc:  # noqa: BLE001
                log.warning("calendar failed: %s (likely atptour.com blocked)", exc)
        if args.mode in ("bios", "full"):
            await push_bios(client, limit=args.limit)
        if args.mode in ("matches", "full"):
            await push_matches(client, limit=args.limit)
        if args.mode in ("elo", "full"):
            await trigger_elo_recompute(client)
    return 0


def main() -> None:
    sys.exit(asyncio.run(amain()))


if __name__ == "__main__":
    main()
