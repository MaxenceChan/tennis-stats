"""
Calcul Elo à partir de la table `matches`.

K-factor :
  - Grand Slam : 40
  - Masters 1000 / ATP Finals : 32
  - ATP 500 : 28
  - ATP 250 / autres : 24

Pondération par différence de rang ATP au moment du match (multiplicateur léger : ±10 %)
pour rendre les upsets contre top-10 un peu plus payants.

Rating de départ : 1500.
Sauvegarde : on stocke le rating courant par (player_id, surface) — surface 'all' = global.
On peut aussi calculer par surface (Hard / Clay / Grass).
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EloRating, Match, Player

logger = logging.getLogger(__name__)

DEFAULT_RATING = 1500.0
K_BY_CATEGORY = {
    "Grand Slam": 40,
    "Masters 1000": 32,
    "ATP Finals": 32,
    "ATP 500": 28,
    "ATP 250": 24,
}


def _k_factor(category: str | None) -> int:
    return K_BY_CATEGORY.get(category or "", 24)


def _rank_modifier(rank_winner: int | None, rank_loser: int | None) -> float:
    """Bonus si le vainqueur est moins bien classé que le perdant (upset)."""
    if not rank_winner or not rank_loser:
        return 1.0
    if rank_winner > rank_loser:
        delta = min(rank_winner - rank_loser, 100)
        return 1.0 + (delta / 100.0) * 0.10
    return 1.0


def _expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + math.pow(10.0, (rb - ra) / 400.0))


def recompute_elo(db: Session, *, surfaces: tuple[str, ...] = ("all",)) -> dict[str, int]:
    """
    Recalcule l'Elo en remettant tout à zéro, dans l'ordre chronologique.
    Retourne le nombre de matches traités par surface.
    """
    counts: dict[str, int] = {}
    for surface in surfaces:
        ratings: dict[int, float] = defaultdict(lambda: DEFAULT_RATING)
        played: dict[int, int] = defaultdict(int)

        q = select(Match).order_by(Match.match_date.asc().nulls_last(), Match.id.asc())
        if surface != "all":
            q = q.join(Match.tournament).where(Match.tournament.has(surface=surface))

        n = 0
        for m in db.execute(q).scalars():
            if not m.winner_id or not m.loser_id:
                continue
            ra = ratings[m.winner_id]
            rb = ratings[m.loser_id]
            ea = _expected(ra, rb)
            k = _k_factor(m.tournament.category if m.tournament else None)
            mod = _rank_modifier(
                rank_winner=m.atp_rank_p1 if m.winner_id == m.player1_id else m.atp_rank_p2,
                rank_loser=m.atp_rank_p2 if m.winner_id == m.player1_id else m.atp_rank_p1,
            )
            delta = k * mod * (1.0 - ea)
            ratings[m.winner_id] = ra + delta
            ratings[m.loser_id] = rb - delta
            played[m.winner_id] += 1
            played[m.loser_id] += 1
            n += 1

        # persist
        existing = {(r.player_id, r.surface): r for r in db.scalars(
            select(EloRating).where(EloRating.surface == surface)
        )}
        for pid, rating in ratings.items():
            row = existing.get((pid, surface))
            if row is None:
                row = EloRating(player_id=pid, surface=surface, rating=rating, matches_played=played[pid])
                db.add(row)
            else:
                row.rating = rating
                row.matches_played = played[pid]
        # also update Player.elo_rating snapshot (surface 'all')
        if surface == "all":
            for pl in db.scalars(select(Player)):
                pl.elo_rating = ratings.get(pl.id, DEFAULT_RATING)
        db.commit()
        counts[surface] = n
        logger.info("Elo recomputed for surface=%s, %d matches processed", surface, n)
    return counts
