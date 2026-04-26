from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, asc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Match, Player, Tournament
from app.schemas.player import PlayerBase
from app.schemas.tournament import TournamentBase, TournamentWithWinner

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=list[TournamentWithWinner])
def calendar(
    year: int | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = select(Tournament).order_by(asc(Tournament.start_date).nulls_last(), Tournament.name)
    if year is not None:
        q = q.where(Tournament.year == year)
    if category:
        q = q.where(Tournament.category == category)
    tournaments = db.scalars(q).all()
    if not tournaments:
        return []

    # Find winner = player who won the final ("F") of each tournament
    tids = [t.id for t in tournaments]
    rows = db.execute(
        select(Match.tournament_id, Player)
        .join(Player, Player.id == Match.winner_id)
        .where(Match.tournament_id.in_(tids), Match.round == "F")
    ).all()
    winners: dict[int, Player] = {tid: player for tid, player in rows}

    out: list[TournamentWithWinner] = []
    for t in tournaments:
        base = TournamentBase.model_validate(t).model_dump()
        winner = winners.get(t.id)
        out.append(TournamentWithWinner(
            **base,
            winner=PlayerBase.model_validate(winner) if winner else None,
        ))
    return out
