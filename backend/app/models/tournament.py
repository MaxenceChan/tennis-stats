from datetime import date, datetime

from sqlalchemy import String, Integer, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"
    __table_args__ = (UniqueConstraint("slug", "year", name="uq_tournament_slug_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(140), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)

    surface: Mapped[str | None] = mapped_column(String(20))        # Hard / Clay / Grass / Carpet
    category: Mapped[str | None] = mapped_column(String(20), index=True)  # ATP 250 / 500 / Masters 1000 / Grand Slam
    city: Mapped[str | None] = mapped_column(String(80))
    country: Mapped[str | None] = mapped_column(String(80))
    start_date: Mapped[date | None] = mapped_column(Date, index=True)
    end_date: Mapped[date | None] = mapped_column(Date)
    draw_size: Mapped[int | None] = mapped_column(Integer)
    prize_money: Mapped[str | None] = mapped_column(String(40))

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
