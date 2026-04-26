from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Match, Player, Tournament
from app.schemas.match import MatchRead, MatchStats, PlayerFullProfile
from app.schemas.player import PlayerBase, PlayerDetail
from app.schemas.tournament import TournamentBase

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/search", response_model=list[PlayerBase])
def search_players(q: str = Query(..., min_length=1), limit: int = 20, db: Session = Depends(get_db)):
    like = f"%{q}%"
    rows = db.scalars(
        select(Player)
        .where(or_(Player.full_name.ilike(like), Player.slug.ilike(like)))
        .order_by(Player.atp_rank.asc().nulls_last())
        .limit(limit)
    ).all()
    return rows


@router.get("/{player_id}", response_model=PlayerDetail)
def get_player(player_id: int, db: Session = Depends(get_db)):
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerDetail.model_validate(p)


def _match_to_read(m: Match, viewpoint_id: int | None = None) -> MatchRead:
    def stats(side: str) -> MatchStats:
        return MatchStats(
            first_serve_pct=getattr(m, f"first_serve_pct_{side}"),
            first_serve_win_pct=getattr(m, f"first_serve_win_pct_{side}"),
            second_serve_win_pct=getattr(m, f"second_serve_win_pct_{side}"),
            break_points_saved=getattr(m, f"break_points_saved_{side}"),
            double_fault_pct=getattr(m, f"double_fault_pct_{side}"),
            dominance_ratio=getattr(m, f"dominance_ratio_{side}"),
            ace_pct=getattr(m, f"ace_pct_{side}"),
        )

    return MatchRead(
        id=m.id, match_date=m.match_date, round=m.round, score=m.score,
        sets_count=m.sets_count, duration_minutes=m.duration_minutes,
        tournament=TournamentBase.model_validate(m.tournament),
        player1=PlayerBase.model_validate(m.player1),
        player2=PlayerBase.model_validate(m.player2),
        winner_id=m.winner_id, loser_id=m.loser_id,
        atp_rank_p1=m.atp_rank_p1, atp_rank_p2=m.atp_rank_p2,
        stats_p1=stats("p1"), stats_p2=stats("p2"),
    )


@router.get("/{player_id}/matches", response_model=list[MatchRead])
def player_matches(player_id: int, limit: int = 50, db: Session = Depends(get_db)):
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    rows = db.scalars(
        select(Match)
        .where(or_(Match.player1_id == player_id, Match.player2_id == player_id))
        .order_by(desc(Match.match_date), desc(Match.id))
        .limit(limit)
    ).all()
    return [_match_to_read(m, viewpoint_id=player_id) for m in rows]


@router.get("/{player_id}/profile", response_model=PlayerFullProfile)
def player_profile(player_id: int, db: Session = Depends(get_db)):
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    matches = db.scalars(
        select(Match)
        .where(or_(Match.player1_id == player_id, Match.player2_id == player_id))
        .order_by(desc(Match.match_date), desc(Match.id))
    ).all()
    recent = [_match_to_read(m, player_id) for m in matches[:20]]
    all_results = [_match_to_read(m, player_id) for m in matches]

    # Calcule des seasons à partir des matches en DB
    from collections import defaultdict
    by_year: dict[int, dict] = defaultdict(lambda: {"wins": 0, "losses": 0, "titles": 0, "finals": 0})
    titles_finals: list[dict] = []
    for m in matches:
        if not m.match_date:
            continue
        y = m.match_date.year
        if m.winner_id == player_id:
            by_year[y]["wins"] += 1
        elif m.loser_id == player_id:
            by_year[y]["losses"] += 1
        if m.round == "F":
            by_year[y]["finals"] += 1
            won = m.winner_id == player_id
            if won:
                by_year[y]["titles"] += 1
            opp = m.player2 if m.player1_id == player_id else m.player1
            titles_finals.append({
                "year": y,
                "tournament": m.tournament.name if m.tournament else None,
                "result": "Champion" if won else "Finalist",
                "opponent_id": opp.id if opp else None,
                "opponent_name": opp.full_name if opp else None,
                "opponent_country": opp.country if opp else None,
                "score": m.score,
            })

    seasons = [
        {"year": y, "wins": v["wins"], "losses": v["losses"],
         "titles": v["titles"], "finals": v["finals"]}
        for y, v in sorted(by_year.items(), reverse=True)
    ]

    # Major events = TOUS les matchs en Grand Slams / Masters 1000 / ATP Finals (carrière complète)
    major_events = []
    for m in matches:
        if m.tournament and m.tournament.category in ("Grand Slam", "Masters 1000", "ATP Finals"):
            opp = m.player2 if m.player1_id == player_id else m.player1
            major_events.append({
                "tournament": m.tournament.name,
                "year": m.tournament.year,
                "round": m.round,
                "result": "W" if m.winner_id == player_id else "L",
                "score": m.score,
                "opponent_id": opp.id if opp else None,
                "opponent_name": opp.full_name if opp else None,
                "opponent_country": opp.country if opp else None,
            })

    return PlayerFullProfile(
        player=PlayerDetail.model_validate(p).model_dump(),
        recent_results=recent,
        all_results=all_results,
        tour_level_seasons=seasons,
        recent_titles_finals=titles_finals,  # carrière complète
        year_end_rankings=[],
        major_recent_events=major_events,
    )
