"""Schémas Pydantic pour les endpoints d'import (POST data depuis GH Actions)."""
from __future__ import annotations

from datetime import date
from pydantic import BaseModel


class RankingEntryIn(BaseModel):
    rank: int
    player_name: str
    country: str | None = None
    points: int | None = None


class RankingsImport(BaseModel):
    atp: list[RankingEntryIn] = []
    race: list[RankingEntryIn] = []


class CalendarEntryIn(BaseModel):
    name: str
    slug: str | None = None
    city: str | None = None
    country: str | None = None
    surface: str | None = None
    category: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CalendarImport(BaseModel):
    entries: list[CalendarEntryIn] = []


class PlayerBioImport(BaseModel):
    full_name: str
    slug: str | None = None
    wikipedia_url: str | None = None
    birth_date: date | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    hand: str | None = None
    backhand: str | None = None


class MatchIn(BaseModel):
    match_date: date | None = None
    tournament_name: str
    surface: str | None = None
    round: str | None = None
    opponent_name: str
    opponent_rank: int | None = None
    own_rank: int | None = None
    result: str = ""  # "W" or "L"
    score: str | None = None
    sets_count: int | None = None
    duration_minutes: int | None = None
    stats: dict[str, float | None] = {}
    source_url: str | None = None


class PlayerMatchesImport(BaseModel):
    owner_full_name: str
    owner_slug: str | None = None
    tennis_abstract_url: str | None = None
    matches: list[MatchIn] = []


class PlayerListItem(BaseModel):
    id: int
    slug: str
    full_name: str
    atp_rank: int | None = None
    has_bio: bool = False
    has_matches: bool = False
