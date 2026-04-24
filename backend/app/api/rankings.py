from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, asc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EloRating, Player
from app.schemas.player import RankingRow

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/atp", response_model=list[RankingRow])
def atp_ranking(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Player)
        .where(Player.atp_rank.is_not(None))
        .order_by(asc(Player.atp_rank))
        .limit(limit)
    ).all()
    return [
        RankingRow(rank=p.atp_rank, player_id=p.id, player_name=p.full_name,
                   country=p.country, points=p.atp_points)
        for p in rows
    ]


@router.get("/race", response_model=list[RankingRow])
def race_ranking(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Player)
        .where(Player.race_rank.is_not(None))
        .order_by(asc(Player.race_rank))
        .limit(limit)
    ).all()
    return [
        RankingRow(rank=p.race_rank, player_id=p.id, player_name=p.full_name,
                   country=p.country, points=p.race_points)
        for p in rows
    ]


@router.get("/elo", response_model=list[RankingRow])
def elo_ranking(
    limit: int = Query(100, le=1000),
    surface: str = Query("all"),
    db: Session = Depends(get_db),
):
    q = (
        select(EloRating, Player)
        .join(Player, Player.id == EloRating.player_id)
        .where(EloRating.surface == surface)
        .order_by(desc(EloRating.rating))
        .limit(limit)
    )
    out: list[RankingRow] = []
    for i, (e, p) in enumerate(db.execute(q).all(), start=1):
        out.append(RankingRow(rank=i, player_id=p.id, player_name=p.full_name,
                              country=p.country, points=round(e.rating, 1)))
    return out
