from datetime import date, datetime

from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    """
    Un match entre deux joueurs. Les champs *_p1 / *_p2 sont indexés par joueur,
    pas par vainqueur — `winner_id` / `loser_id` indiquent le résultat.
    """
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("tournament_id", "round", "player1_id", "player2_id", name="uq_match"),
        Index("ix_match_date", "match_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), index=True)
    round: Mapped[str | None] = mapped_column(String(10))  # R128, R64, …, QF, SF, F
    match_date: Mapped[date | None] = mapped_column(Date)

    player1_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    player2_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    loser_id: Mapped[int | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))

    score: Mapped[str | None] = mapped_column(String(80))           # "6-4 7-5" etc.
    sets_count: Mapped[int | None] = mapped_column(Integer)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    atp_rank_p1: Mapped[int | None] = mapped_column(Integer)
    atp_rank_p2: Mapped[int | None] = mapped_column(Integer)

    first_serve_pct_p1: Mapped[float | None] = mapped_column(Float)
    first_serve_pct_p2: Mapped[float | None] = mapped_column(Float)
    first_serve_win_pct_p1: Mapped[float | None] = mapped_column(Float)
    first_serve_win_pct_p2: Mapped[float | None] = mapped_column(Float)
    second_serve_win_pct_p1: Mapped[float | None] = mapped_column(Float)
    second_serve_win_pct_p2: Mapped[float | None] = mapped_column(Float)
    break_points_saved_p1: Mapped[float | None] = mapped_column(Float)
    break_points_saved_p2: Mapped[float | None] = mapped_column(Float)
    double_fault_pct_p1: Mapped[float | None] = mapped_column(Float)
    double_fault_pct_p2: Mapped[float | None] = mapped_column(Float)
    dominance_ratio_p1: Mapped[float | None] = mapped_column(Float)
    dominance_ratio_p2: Mapped[float | None] = mapped_column(Float)
    ace_pct_p1: Mapped[float | None] = mapped_column(Float)
    ace_pct_p2: Mapped[float | None] = mapped_column(Float)

    source_url: Mapped[str | None] = mapped_column(String(400))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tournament = relationship("Tournament", lazy="joined")
    player1 = relationship("Player", foreign_keys=[player1_id], lazy="joined")
    player2 = relationship("Player", foreign_keys=[player2_id], lazy="joined")
