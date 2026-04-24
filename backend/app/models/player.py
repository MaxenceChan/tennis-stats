from datetime import date, datetime

from sqlalchemy import String, Integer, Float, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("slug", name="uq_players_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    first_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str | None] = mapped_column(String(80))
    full_name: Mapped[str] = mapped_column(String(160), index=True)

    country: Mapped[str | None] = mapped_column(String(3))
    birth_date: Mapped[date | None] = mapped_column(Date)
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    hand: Mapped[str | None] = mapped_column(String(1))          # R/L
    backhand: Mapped[str | None] = mapped_column(String(1))      # 1/2

    atp_rank: Mapped[int | None] = mapped_column(Integer, index=True)
    atp_points: Mapped[int | None] = mapped_column(Integer)
    race_rank: Mapped[int | None] = mapped_column(Integer, index=True)
    race_points: Mapped[int | None] = mapped_column(Integer)
    elo_rating: Mapped[float | None] = mapped_column(Float, index=True)

    wikipedia_url: Mapped[str | None] = mapped_column(String(400))
    tennis_abstract_url: Mapped[str | None] = mapped_column(String(400))

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def age(self, today: date | None = None) -> int | None:
        if self.birth_date is None:
            return None
        today = today or date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years
