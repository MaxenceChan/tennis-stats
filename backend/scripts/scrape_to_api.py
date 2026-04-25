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

from app.scrapers import atp_calendar, balldontlie, live_tennis, sackmann, tennis_abstract, wikipedia
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


# ---------------------------- Sackmann (raw.githubusercontent.com) -------------

CHUNK_SIZE = 500


def _chunked(iterable, size):
    buf = []
    for it in iterable:
        buf.append(it)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


async def push_sackmann_players(client: httpx.AsyncClient) -> None:
    log.info("Fetching Sackmann atp_players.csv...")
    players = await sackmann.fetch_players(client)
    log.info("  -> %d players. Pushing in chunks of %d...", len(players), CHUNK_SIZE)
    total = 0
    for i, chunk in enumerate(_chunked(players, CHUNK_SIZE), 1):
        payload = {"players": [
            {
                "sackmann_id": p.player_id,
                "full_name": p.full_name,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "country": p.country,
                "birth_date": p.birth_date.isoformat() if p.birth_date else None,
                "height_cm": p.height_cm,
                "hand": p.hand,
                "wikidata_id": p.wikidata_id,
            }
            for p in chunk
        ]}
        res = await post_json(client, "/api/admin/import/sackmann-players", payload)
        total += res.get("ingested", 0)
        log.info("  chunk %d: ingested=%s (total=%d)", i, res.get("ingested"), total)
    log.info("DONE players: %d", total)


async def push_sackmann_rankings(client: httpx.AsyncClient) -> None:
    log.info("Fetching Sackmann atp_rankings_current.csv (latest week only)...")
    rows = await sackmann.fetch_current_rankings(client, latest_only=True)
    if not rows:
        log.warning("No rankings returned")
        return
    payload = {
        "ranking_date": rows[0].ranking_date.isoformat(),
        "rankings": [
            {"sackmann_id": r.player_id, "rank": r.rank, "points": r.points}
            for r in rows
        ],
    }
    log.info("POST /api/admin/import/sackmann-rankings (%d rows, date=%s)...",
             len(rows), payload["ranking_date"])
    res = await post_json(client, "/api/admin/import/sackmann-rankings", payload)
    log.info("  -> %s", res)


async def push_sackmann_matches(client: httpx.AsyncClient, years: list[int]) -> None:
    for year in years:
        log.info("Fetching Sackmann atp_matches_%d.csv...", year)
        try:
            matches = await sackmann.fetch_matches_year(client, year)
        except Exception as exc:  # noqa: BLE001
            log.warning("  year %d failed: %s", year, exc)
            continue
        if not matches:
            continue
        log.info("  -> %d matches. Pushing in chunks of %d...", len(matches), CHUNK_SIZE)
        total = 0
        for i, chunk in enumerate(_chunked(matches, CHUNK_SIZE), 1):
            payload = {"matches": [
                {
                    "tourney_id": m.tourney_id,
                    "tourney_name": m.tourney_name,
                    "surface": m.surface,
                    "draw_size": m.draw_size,
                    "category": sackmann.category_for(m.tourney_level, m.draw_size),
                    "tourney_date": m.tourney_date.isoformat() if m.tourney_date else None,
                    "match_num": m.match_num,
                    "winner_sackmann_id": m.winner_id,
                    "winner_name": m.winner_name,
                    "loser_sackmann_id": m.loser_id,
                    "loser_name": m.loser_name,
                    "score": m.score,
                    "best_of": m.best_of,
                    "round": m.round,
                    "minutes": m.minutes,
                    "w_stats": m.w_stats,
                    "l_stats": m.l_stats,
                    "winner_rank": m.winner_rank,
                    "loser_rank": m.loser_rank,
                }
                for m in chunk
            ]}
            res = await post_json(client, "/api/admin/import/sackmann-matches", payload)
            total += res.get("ingested", 0)
            if i % 5 == 0:
                log.info("  chunk %d: ingested=%s (total=%d)", i, res.get("ingested"), total)
        log.info("DONE year %d: %d new matches", year, total)


# ---------------------------- BallDontLie (current data) ----------------------

async def push_bdl_rankings(client: httpx.AsyncClient) -> None:
    log.info("Fetching BallDontLie current rankings...")
    rows = await balldontlie.fetch_rankings()
    if not rows:
        log.warning("BDL rankings empty — skipping push")
        return
    rdate = rows[0].ranking_date or date.today()
    log.info("  -> %d rankings, date=%s", len(rows), rdate)
    payload = {
        "ranking_date": rdate.isoformat(),
        "rankings": [
            {
                "bdl_id": r.player_bdl_id,
                "full_name": r.full_name,
                "rank": r.rank,
                "points": r.points,
                "movement": r.movement,
            }
            for r in rows if r.player_bdl_id and r.rank
        ],
    }
    res = await post_json(client, "/api/admin/import/bdl-rankings", payload)
    log.info("  -> %s", res)


async def push_bdl_tournaments(client: httpx.AsyncClient,
                                seasons: list[int] | None = None) -> None:
    seasons = seasons or [date.today().year]
    for season in seasons:
        log.info("Fetching BDL tournaments season=%d ...", season)
        rows = await balldontlie.fetch_tournaments(season=season)
        log.info("  -> %d tournaments", len(rows))
        if not rows:
            continue
        payload = {
            "tournaments": [
                {
                    "bdl_id": t.bdl_id,
                    "name": t.name,
                    "location": t.location,
                    "surface": t.surface,
                    "category": t.category,
                    "season": t.season,
                    "start_date": t.start_date.isoformat() if t.start_date else None,
                    "end_date": t.end_date.isoformat() if t.end_date else None,
                    "draw_size": t.draw_size,
                }
                for t in rows
            ],
        }
        res = await post_json(client, "/api/admin/import/bdl-tournaments", payload)
        log.info("  -> %s", res)


# ---------------------------- Probe (test from runner IP) ----------------------

async def probe(client: httpx.AsyncClient) -> None:
    targets = {
        "live-tennis.eu": "https://live-tennis.eu/en/atp-live-ranking",
        "tennisabstract.com": "https://www.tennisabstract.com/cgi-bin/player.cgi?p=CarlosAlcaraz",
        "wikipedia.org": "https://en.wikipedia.org/wiki/ATP_Rankings",
        "atptour.com": "https://www.atptour.com/en/rankings/singles",
        "raw.githubusercontent.com": "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_rankings_current.csv",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for name, url in targets.items():
        try:
            r = await client.get(url, headers=headers, timeout=20.0)
            log.info("PROBE %-30s -> %d (%d bytes)", name, r.status_code, len(r.content))
        except Exception as exc:  # noqa: BLE001
            log.info("PROBE %-30s -> ERROR %s: %s", name, type(exc).__name__, exc)


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
    parser.add_argument("mode", choices=[
        "probe",
        "rankings", "calendar", "bios", "matches",
        "sackmann", "sackmann-players", "sackmann-rankings", "sackmann-matches",
        "bdl", "bdl-rankings", "bdl-tournaments",
        "elo", "full",
    ])
    parser.add_argument("--limit", type=int, default=50,
                        help="Number of players to enrich (bios/matches)")
    parser.add_argument("--rankings-limit", type=int, default=1000,
                        help="Max rank to import")
    parser.add_argument("--years", type=str, default="2024",
                        help="Sackmann match years, comma-separated (e.g. 2022,2023,2024)")
    args = parser.parse_args()

    years = [int(y.strip()) for y in args.years.split(",") if y.strip().isdigit()]

    async with httpx.AsyncClient() as client:
        if args.mode == "probe":
            await probe(client)
            return 0
        # Sackmann pipeline (recommended path)
        if args.mode in ("sackmann", "full", "sackmann-players"):
            await push_sackmann_players(client)
        if args.mode in ("sackmann", "full", "sackmann-rankings"):
            await push_sackmann_rankings(client)
        if args.mode in ("sackmann", "full", "sackmann-matches"):
            await push_sackmann_matches(client, years=years)
        # BallDontLie (current rankings + calendar — fills the post-Sackmann gap)
        if args.mode in ("bdl", "full", "bdl-rankings"):
            await push_bdl_rankings(client)
        if args.mode in ("bdl", "full", "bdl-tournaments"):
            await push_bdl_tournaments(client, seasons=[date.today().year])
        # Legacy/live sources (will fail from blocked IPs — kept for compat)
        if args.mode == "rankings":
            await push_rankings(client, limit=args.rankings_limit)
        if args.mode == "calendar":
            await push_calendar(client)
        if args.mode == "bios":
            await push_bios(client, limit=args.limit)
        if args.mode == "matches":
            await push_matches(client, limit=args.limit)
        if args.mode in ("elo", "full"):
            await trigger_elo_recompute(client)
    return 0


def main() -> None:
    sys.exit(asyncio.run(amain()))


if __name__ == "__main__":
    main()
