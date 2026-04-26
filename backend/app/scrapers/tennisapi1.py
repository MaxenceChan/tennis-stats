"""TennisApi1 (RapidAPI) — données live (matches en cours + classement live).

Quota Basic free : 60 req / mois — usage parcimonieux. Caching 60 s côté API.

Endpoints utilisés :
  GET /api/tennis/rankings/atp/live   → classement ATP en temps réel
  GET /api/tennis/events/live         → matchs en cours sur le circuit ATP/WTA/Challenger

Auth : header `X-RapidAPI-Key: <RAPIDAPI_KEY>` + `X-RapidAPI-Host: tennisapi1.p.rapidapi.com`.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

HOST = "tennisapi1.p.rapidapi.com"
BASE_URL = f"https://{HOST}"


@dataclass
class LiveRankingRow:
    rank: int
    previous_rank: int | None
    player_name: str
    country: str | None     # alpha3
    points: int | None
    tournaments_played: int | None


@dataclass
class LivePlayer:
    name: str
    country: str | None     # alpha3
    ranking: int | None


@dataclass
class LiveSetScore:
    set_number: int
    home: int | None
    away: int | None
    home_tiebreak: int | None
    away_tiebreak: int | None


@dataclass
class LiveMatch:
    id: int
    status: str             # "inprogress" | "finished" | ...
    home: LivePlayer
    away: LivePlayer
    home_score_current: int | None
    away_score_current: int | None
    home_point: str | None  # "0", "15", "30", "40", "A"
    away_point: str | None
    sets: list[LiveSetScore]
    winner_code: int | None  # null in progress, 1 = home, 2 = away
    server_code: int | None  # 1 home / 2 away
    start_timestamp: int | None
    tournament_name: str | None
    tournament_category: str | None
    surface: str | None
    round_name: str | None


def _api_key() -> str:
    key = os.environ.get("RAPIDAPI_KEY", "").strip()
    if not key:
        raise RuntimeError("RAPIDAPI_KEY env var missing")
    return key


def _headers() -> dict[str, str]:
    return {"X-RapidAPI-Key": _api_key(), "X-RapidAPI-Host": HOST}


async def _get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{BASE_URL}{path}", headers=_headers())
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------- public API


async def fetch_live_rankings() -> list[LiveRankingRow]:
    body = await _get("/api/tennis/rankings/atp/live")
    out: list[LiveRankingRow] = []
    for row in body.get("rankings") or []:
        team = row.get("team") or {}
        country = (team.get("country") or {}).get("alpha3")
        out.append(LiveRankingRow(
            rank=row.get("ranking"),
            previous_rank=row.get("previousRanking"),
            player_name=team.get("name") or "",
            country=country,
            points=row.get("points"),
            tournaments_played=row.get("tournamentsPlayed"),
        ))
    return out


def _player(team: dict | None) -> LivePlayer:
    team = team or {}
    country = (team.get("country") or {}).get("alpha3")
    return LivePlayer(
        name=team.get("name") or "",
        country=country,
        ranking=team.get("ranking"),
    )


def _sets(home_score: dict, away_score: dict) -> list[LiveSetScore]:
    sets: list[LiveSetScore] = []
    for i in range(1, 6):
        key = f"period{i}"
        if key in home_score or key in away_score:
            sets.append(LiveSetScore(
                set_number=i,
                home=home_score.get(key),
                away=away_score.get(key),
                home_tiebreak=home_score.get(f"{key}TieBreak"),
                away_tiebreak=away_score.get(f"{key}TieBreak"),
            ))
    return sets


async def fetch_live_matches() -> list[LiveMatch]:
    body = await _get("/api/tennis/events/live")
    out: list[LiveMatch] = []
    for ev in body.get("events") or []:
        home_score = ev.get("homeScore") or {}
        away_score = ev.get("awayScore") or {}
        tour = ev.get("tournament") or {}
        unique = tour.get("uniqueTournament") or {}
        status = (ev.get("status") or {}).get("type") or ""
        out.append(LiveMatch(
            id=ev.get("id"),
            status=status,
            home=_player(ev.get("homeTeam")),
            away=_player(ev.get("awayTeam")),
            home_score_current=home_score.get("current"),
            away_score_current=away_score.get("current"),
            home_point=str(home_score.get("point")) if home_score.get("point") is not None else None,
            away_point=str(away_score.get("point")) if away_score.get("point") is not None else None,
            sets=_sets(home_score, away_score),
            winner_code=ev.get("winnerCode"),
            server_code=(ev.get("serve") or {}).get("code") if isinstance(ev.get("serve"), dict) else ev.get("serve"),
            start_timestamp=ev.get("startTimestamp"),
            tournament_name=unique.get("name") or tour.get("name"),
            tournament_category=(unique.get("category") or {}).get("name") if isinstance(unique.get("category"), dict) else None,
            surface=unique.get("groundType"),
            round_name=(ev.get("roundInfo") or {}).get("name"),
        ))
    return out
