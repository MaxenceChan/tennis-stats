from datetime import date
from pydantic import BaseModel, ConfigDict

from app.schemas.player import PlayerBase


class TournamentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    year: int
    surface: str | None = None
    category: str | None = None
    city: str | None = None
    country: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    draw_size: int | None = None


class TournamentWithWinner(TournamentBase):
    winner: PlayerBase | None = None
