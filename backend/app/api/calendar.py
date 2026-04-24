from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, asc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tournament
from app.schemas.tournament import TournamentBase

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=list[TournamentBase])
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
    return db.scalars(q).all()
