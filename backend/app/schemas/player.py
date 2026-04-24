from datetime import date
from pydantic import BaseModel, ConfigDict


class PlayerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    full_name: str
    country: str | None = None
    atp_rank: int | None = None
    race_rank: int | None = None
    elo_rating: float | None = None


class PlayerDetail(PlayerBase):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None
    age: int | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    hand: str | None = None
    backhand: str | None = None
    atp_points: int | None = None
    race_points: int | None = None
    wikipedia_url: str | None = None
    tennis_abstract_url: str | None = None


class RankingRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    player_id: int
    player_name: str
    country: str | None = None
    points: int | float | None = None
