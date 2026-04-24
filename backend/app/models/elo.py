from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EloRating(Base):
    """
    Historique Elo par joueur et par surface. `surface='all'` = rating global.
    """
    __tablename__ = "elo_ratings"
    __table_args__ = (
        UniqueConstraint("player_id", "surface", name="uq_elo_player_surface"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    surface: Mapped[str] = mapped_column(String(20), default="all", index=True)
    rating: Mapped[float] = mapped_column(Float, default=1500.0)
    matches_played: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
