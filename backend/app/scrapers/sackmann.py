"""
Scraper Jeff Sackmann tennis_atp dataset (CSV publics sur GitHub).

Sources :
  https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_players.csv
  https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_rankings_current.csv
  https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv

Avantages : hébergé sur raw.githubusercontent.com → jamais blacklisté.
Inconvénients : mises à jour ~hebdo par Sackmann lui-même, pas du temps réel.
Couverture : tout l'historique ATP + bios + stats détaillées des matchs.
"""
from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"

# tourney_level → catégorie lisible
LEVEL_CATEGORY = {
    "G": "Grand Slam",
    "M": "Masters 1000",
    "F": "ATP Finals",
    "D": "Davis Cup",
    "O": "Olympics",
    "A": "ATP",  # ATP 250/500 — distinction faite via draw_size
}


@dataclass
class SackmannPlayer:
    player_id: int
    full_name: str
    first_name: str | None
    last_name: str | None
    country: str | None
    birth_date: date | None
    height_cm: int | None
    hand: str | None
    wikidata_id: str | None


@dataclass
class SackmannRanking:
    ranking_date: date
    rank: int
    player_id: int
    points: int | None


@dataclass
class SackmannMatch:
    tourney_id: str
    tourney_name: str
    surface: str | None
    draw_size: int | None
    tourney_level: str | None
    tourney_date: date | None
    match_num: int | None
    winner_id: int | None
    winner_name: str | None
    loser_id: int | None
    loser_name: str | None
    score: str | None
    best_of: int | None
    round: str | None
    minutes: int | None
    w_stats: dict[str, float | int | None] = field(default_factory=dict)
    l_stats: dict[str, float | int | None] = field(default_factory=dict)
    winner_rank: int | None = None
    winner_rank_points: int | None = None
    loser_rank: int | None = None
    loser_rank_points: int | None = None


def _parse_int(v: str | None) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _parse_date_yyyymmdd(v: str | None) -> date | None:
    if not v or len(v) < 8:
        return None
    try:
        return datetime.strptime(v[:8], "%Y%m%d").date()
    except ValueError:
        return None


def _safe_pct(num: str | None, den: str | None) -> float | None:
    n = _parse_int(num)
    d = _parse_int(den)
    if n is None or d is None or d == 0:
        return None
    return round(100.0 * n / d, 1)


async def _fetch_csv(client: httpx.AsyncClient, path: str) -> str:
    url = f"{BASE_URL}/{path}"
    logger.info("Fetching %s", url)
    r = await client.get(url, timeout=httpx.Timeout(60.0, connect=20.0))
    r.raise_for_status()
    return r.text


async def fetch_players(client: httpx.AsyncClient) -> list[SackmannPlayer]:
    text = await _fetch_csv(client, "atp_players.csv")
    out: list[SackmannPlayer] = []
    for row in csv.DictReader(io.StringIO(text)):
        first = row.get("name_first", "").strip()
        last = row.get("name_last", "").strip()
        full = f"{first} {last}".strip()
        if not full:
            continue
        out.append(SackmannPlayer(
            player_id=_parse_int(row["player_id"]) or 0,
            full_name=full,
            first_name=first or None,
            last_name=last or None,
            country=(row.get("ioc") or "").strip() or None,
            birth_date=_parse_date_yyyymmdd(row.get("dob")),
            height_cm=_parse_int(row.get("height")),
            hand=(row.get("hand") or "").strip()[:1] or None,
            wikidata_id=(row.get("wikidata_id") or "").strip() or None,
        ))
    logger.info("Parsed %d players", len(out))
    return out


async def fetch_current_rankings(client: httpx.AsyncClient,
                                 latest_only: bool = True) -> list[SackmannRanking]:
    """Le fichier atp_rankings_current.csv contient toutes les snapshots
    hebdo de la décennie courante. On garde par défaut uniquement la plus
    récente (latest_only=True)."""
    text = await _fetch_csv(client, "atp_rankings_current.csv")
    rows: list[SackmannRanking] = []
    for row in csv.DictReader(io.StringIO(text)):
        d = _parse_date_yyyymmdd(row.get("ranking_date"))
        rk = _parse_int(row.get("rank"))
        pid = _parse_int(row.get("player"))
        if d is None or rk is None or pid is None:
            continue
        rows.append(SackmannRanking(
            ranking_date=d, rank=rk, player_id=pid,
            points=_parse_int(row.get("points")),
        ))
    if not latest_only:
        return rows
    if not rows:
        return rows
    last_date = max(r.ranking_date for r in rows)
    latest = [r for r in rows if r.ranking_date == last_date]
    logger.info("Latest ranking date: %s (%d players)", last_date, len(latest))
    return latest


async def fetch_matches_year(client: httpx.AsyncClient, year: int) -> list[SackmannMatch]:
    """Récupère les matchs ATP d'une année. 404 si l'année n'existe pas."""
    try:
        text = await _fetch_csv(client, f"atp_matches_{year}.csv")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            logger.info("No matches file for %d (404)", year)
            return []
        raise
    out: list[SackmannMatch] = []
    for row in csv.DictReader(io.StringIO(text)):
        w_svpt = _parse_int(row.get("w_svpt"))
        l_svpt = _parse_int(row.get("l_svpt"))
        w_1stIn = _parse_int(row.get("w_1stIn"))
        l_1stIn = _parse_int(row.get("l_1stIn"))

        w_stats = {
            "ace_pct": _safe_pct(row.get("w_ace"), row.get("w_svpt")),
            "double_fault_pct": _safe_pct(row.get("w_df"), row.get("w_svpt")),
            "first_serve_pct": _safe_pct(row.get("w_1stIn"), row.get("w_svpt")),
            "first_serve_win_pct": _safe_pct(row.get("w_1stWon"), row.get("w_1stIn")),
            "second_serve_win_pct": (
                round(100.0 * _parse_int(row.get("w_2ndWon")) / max(1, (w_svpt or 0) - (w_1stIn or 0)), 1)
                if w_svpt and w_1stIn is not None and (w_svpt - w_1stIn) > 0
                and _parse_int(row.get("w_2ndWon")) is not None else None
            ),
            "break_points_saved_pct": _safe_pct(row.get("w_bpSaved"), row.get("w_bpFaced")),
        }
        l_stats = {
            "ace_pct": _safe_pct(row.get("l_ace"), row.get("l_svpt")),
            "double_fault_pct": _safe_pct(row.get("l_df"), row.get("l_svpt")),
            "first_serve_pct": _safe_pct(row.get("l_1stIn"), row.get("l_svpt")),
            "first_serve_win_pct": _safe_pct(row.get("l_1stWon"), row.get("l_1stIn")),
            "second_serve_win_pct": (
                round(100.0 * _parse_int(row.get("l_2ndWon")) / max(1, (l_svpt or 0) - (l_1stIn or 0)), 1)
                if l_svpt and l_1stIn is not None and (l_svpt - l_1stIn) > 0
                and _parse_int(row.get("l_2ndWon")) is not None else None
            ),
            "break_points_saved_pct": _safe_pct(row.get("l_bpSaved"), row.get("l_bpFaced")),
        }

        out.append(SackmannMatch(
            tourney_id=(row.get("tourney_id") or "").strip(),
            tourney_name=(row.get("tourney_name") or "").strip(),
            surface=(row.get("surface") or "").strip() or None,
            draw_size=_parse_int(row.get("draw_size")),
            tourney_level=(row.get("tourney_level") or "").strip() or None,
            tourney_date=_parse_date_yyyymmdd(row.get("tourney_date")),
            match_num=_parse_int(row.get("match_num")),
            winner_id=_parse_int(row.get("winner_id")),
            winner_name=(row.get("winner_name") or "").strip() or None,
            loser_id=_parse_int(row.get("loser_id")),
            loser_name=(row.get("loser_name") or "").strip() or None,
            score=(row.get("score") or "").strip() or None,
            best_of=_parse_int(row.get("best_of")),
            round=(row.get("round") or "").strip() or None,
            minutes=_parse_int(row.get("minutes")),
            w_stats=w_stats,
            l_stats=l_stats,
            winner_rank=_parse_int(row.get("winner_rank")),
            winner_rank_points=_parse_int(row.get("winner_rank_points")),
            loser_rank=_parse_int(row.get("loser_rank")),
            loser_rank_points=_parse_int(row.get("loser_rank_points")),
        ))
    logger.info("Year %d: %d matches", year, len(out))
    return out


def category_for(level: str | None, draw_size: int | None) -> str | None:
    if not level:
        return None
    if level == "A":
        # ATP 250 vs 500 selon draw_size : 28/32 -> 250 ; 48/56 -> 500 (heuristique)
        if draw_size and draw_size >= 48:
            return "ATP 500"
        if draw_size:
            return "ATP 250"
        return "ATP"
    return LEVEL_CATEGORY.get(level, level)


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s
