from datetime import date
from pydantic import BaseModel, ConfigDict

from app.schemas.player import PlayerBase
from app.schemas.tournament import TournamentBase


class MatchStats(BaseModel):
    first_serve_pct: float | None = None
    first_serve_win_pct: float | None = None
    second_serve_win_pct: float | None = None
    break_points_saved: float | None = None
    double_fault_pct: float | None = None
    dominance_ratio: float | None = None
    ace_pct: float | None = None


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_date: date | None
    round: str | None
    score: str | None
    sets_count: int | None
    duration_minutes: int | None

    tournament: TournamentBase
    player1: PlayerBase
    player2: PlayerBase
    winner_id: int | None
    loser_id: int | None

    atp_rank_p1: int | None = None
    atp_rank_p2: int | None = None

    stats_p1: MatchStats | None = None
    stats_p2: MatchStats | None = None


class PlayerResultsBlock(BaseModel):
    """Bloc de résultats à la Tennis Abstract (All-Results, Recent, etc.)."""
    title: str
    matches: list[MatchRead]


class SeasonRow(BaseModel):
    year: int
    wins: int
    losses: int
    titles: int
    finals: int
    year_end_rank: int | None = None


class PlayerFullProfile(BaseModel):
    player: dict
    recent_results: list[MatchRead]
    all_results: list[MatchRead]
    tour_level_seasons: list[SeasonRow]
    recent_titles_finals: list[dict]
    year_end_rankings: list[dict]
    major_recent_events: list[dict]
