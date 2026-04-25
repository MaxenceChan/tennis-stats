"""
Pipelines d'ingestion : transforment les sorties de scrapers en lignes DB.
Chaque fonction est idempotente (upsert sur slug / unique constraints).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Match, Player, Tournament
from app.scrapers import live_tennis, tennis_abstract, wikipedia, atp_calendar
from app.scrapers.live_tennis import RankingEntry, slugify
from app.scrapers.tennis_abstract import ScrapedMatch

logger = logging.getLogger(__name__)


# ---------------------------- Players & rankings --------------------------------

def _upsert_player(db: Session, *, full_name: str, slug: str | None = None,
                   country: str | None = None) -> Player:
    slug = slug or slugify(full_name)
    p = db.scalar(select(Player).where(Player.slug == slug))
    if p is None:
        parts = full_name.split()
        p = Player(
            slug=slug,
            full_name=full_name,
            first_name=parts[0] if parts else None,
            last_name=" ".join(parts[1:]) if len(parts) > 1 else None,
            country=country,
        )
        db.add(p)
        db.flush()
    elif country and not p.country:
        p.country = country
    return p


def ingest_rankings(db: Session, *, atp: list[RankingEntry], race: list[RankingEntry]) -> int:
    by_slug: dict[str, dict] = {}
    for r in atp:
        by_slug.setdefault(slugify(r.player_name), {}).update(
            {"name": r.player_name, "country": r.country, "atp_rank": r.rank, "atp_points": r.points}
        )
    for r in race:
        by_slug.setdefault(slugify(r.player_name), {}).update(
            {"name": r.player_name, "country": r.country, "race_rank": r.rank, "race_points": r.points}
        )
    for slug, data in by_slug.items():
        p = _upsert_player(db, full_name=data["name"], slug=slug, country=data.get("country"))
        p.atp_rank = data.get("atp_rank")
        p.atp_points = data.get("atp_points")
        p.race_rank = data.get("race_rank")
        p.race_points = data.get("race_points")
    db.commit()
    logger.info("Ingested %d players from rankings", len(by_slug))
    return len(by_slug)


# ---------------------------- Wikipedia bios ------------------------------------

async def enrich_player_bios(db: Session, *, max_players: int = 1000) -> int:
    """Pour les joueurs sans birth_date connu, va chercher l'infobox Wikipedia."""
    players = list(db.scalars(
        select(Player)
        .where(Player.birth_date.is_(None))
        .order_by(Player.atp_rank.asc().nulls_last())
        .limit(max_players)
    ))
    n = 0
    for p in players:
        try:
            bio = await wikipedia.fetch_player_bio(p.full_name)
        except Exception as exc:
            logger.warning("Wiki failed for %s: %s", p.full_name, exc)
            continue
        if bio.url:
            p.wikipedia_url = bio.url
        if bio.birth_date:
            p.birth_date = bio.birth_date
        if bio.height_cm:
            p.height_cm = bio.height_cm
        if bio.weight_kg:
            p.weight_kg = bio.weight_kg
        if bio.hand:
            p.hand = bio.hand
        if bio.backhand:
            p.backhand = bio.backhand
        n += 1
        if n % 25 == 0:
            db.commit()
    db.commit()
    logger.info("Enriched %d player bios", n)
    return n


# ---------------------------- Tennis Abstract matches ---------------------------

def _upsert_tournament(db: Session, *, name: str, year: int, surface: str | None) -> Tournament:
    slug = name.lower().replace(" ", "-")
    t = db.scalar(select(Tournament).where(Tournament.slug == slug, Tournament.year == year))
    if t is None:
        t = Tournament(slug=slug, name=name, year=year, surface=surface)
        db.add(t)
        db.flush()
    elif surface and not t.surface:
        t.surface = surface
    return t


def _ingest_match(db: Session, *, owner: Player, sm: ScrapedMatch) -> Match | None:
    if not sm.opponent_name or not sm.tournament_name:
        return None
    year = sm.match_date.year if sm.match_date else datetime.utcnow().year
    tourney = _upsert_tournament(db, name=sm.tournament_name, year=year, surface=sm.surface)
    opp = _upsert_player(db, full_name=sm.opponent_name)

    # Détermine le sens (player1 = owner pour stabilité)
    p1, p2 = owner, opp
    winner_id = owner.id if sm.result == "W" else opp.id if sm.result == "L" else None
    loser_id = opp.id if sm.result == "W" else owner.id if sm.result == "L" else None

    # Idempotence : (tournament, round, p1, p2) ou symétrique
    existing = db.scalar(
        select(Match).where(
            Match.tournament_id == tourney.id,
            Match.round == sm.round,
            ((Match.player1_id == p1.id) & (Match.player2_id == p2.id))
            | ((Match.player1_id == p2.id) & (Match.player2_id == p1.id)),
        )
    )
    stats = sm.stats or {}
    if existing is None:
        m = Match(
            tournament_id=tourney.id,
            round=sm.round,
            match_date=sm.match_date,
            player1_id=p1.id,
            player2_id=p2.id,
            winner_id=winner_id,
            loser_id=loser_id,
            score=sm.score,
            sets_count=sm.sets_count,
            duration_minutes=sm.duration_minutes,
            atp_rank_p1=sm.own_rank,
            atp_rank_p2=sm.opponent_rank,
            ace_pct_p1=stats.get("ace_pct"),
            double_fault_pct_p1=stats.get("double_fault_pct"),
            first_serve_pct_p1=stats.get("first_serve_pct"),
            first_serve_win_pct_p1=stats.get("first_serve_win_pct"),
            second_serve_win_pct_p1=stats.get("second_serve_win_pct"),
            break_points_saved_p1=stats.get("break_points_saved"),
            dominance_ratio_p1=stats.get("dominance_ratio"),
            source_url=sm.source_url,
        )
        db.add(m)
        return m
    else:
        # complète les champs manquants éventuels (autres stats côté p2)
        if existing.player1_id == owner.id:
            existing.atp_rank_p1 = existing.atp_rank_p1 or sm.own_rank
        else:
            existing.atp_rank_p2 = existing.atp_rank_p2 or sm.own_rank
        return existing


async def ingest_player_matches(db: Session, player: Player) -> int:
    slug_ta = tennis_abstract.player_slug_for_url(player.full_name)
    profile = await tennis_abstract.fetch_player_profile(slug_ta)
    if profile.matches:
        player.tennis_abstract_url = f"{tennis_abstract.PLAYER_URL}?p={slug_ta}"
    n = 0
    for sm in profile.matches:
        if _ingest_match(db, owner=player, sm=sm):
            n += 1
    db.commit()
    logger.info("Ingested %d matches for %s", n, player.full_name)
    return n


async def ingest_all_players_matches(db: Session, *, top_n: int = 1000, concurrency: int = 1) -> int:
    players = list(db.scalars(
        select(Player).order_by(Player.atp_rank.asc().nulls_last()).limit(top_n)
    ))
    sem = asyncio.Semaphore(concurrency)
    total = 0

    async def _one(p: Player) -> int:
        async with sem:
            try:
                return await ingest_player_matches(db, p)
            except Exception as exc:
                logger.warning("TA failed for %s: %s", p.full_name, exc)
                return 0

    results = await asyncio.gather(*(_one(p) for p in players))
    total = sum(results)
    return total


# ---------------------------- ATP calendar / categories -------------------------

def ingest_calendar(db: Session, entries: list) -> int:
    n = 0
    for e in entries:
        if not e.name:
            continue
        year = e.start_date.year if e.start_date else datetime.utcnow().year
        t = _upsert_tournament(db, name=e.name, year=year, surface=e.surface)
        if e.category:
            t.category = e.category
        if e.city:
            t.city = e.city
        if e.country:
            t.country = e.country
        if e.start_date:
            t.start_date = e.start_date
        if e.end_date:
            t.end_date = e.end_date
        n += 1
    db.commit()
    return n


# ---------------------------- top-level entry points ---------------------------

async def run_rankings_pipeline(db: Session) -> int:
    atp, race = await asyncio.gather(
        live_tennis.fetch_atp_live(1000),
        live_tennis.fetch_atp_race(1000),
    )
    return ingest_rankings(db, atp=atp, race=race)


async def run_calendar_pipeline(db: Session) -> int:
    entries = await atp_calendar.fetch_calendar()
    return ingest_calendar(db, entries)


# ---------------------------- Import variants (dict-based, for GH Actions push) ---

def ingest_rankings_dicts(db: Session, *, atp: list[dict], race: list[dict]) -> int:
    """Variante de ingest_rankings qui accepte des dicts (depuis HTTP POST)."""
    atp_entries = [RankingEntry(rank=r["rank"], player_name=r["player_name"],
                                country=r.get("country"), points=r.get("points"),
                                player_href=None) for r in atp]
    race_entries = [RankingEntry(rank=r["rank"], player_name=r["player_name"],
                                 country=r.get("country"), points=r.get("points"),
                                 player_href=None) for r in race]
    return ingest_rankings(db, atp=atp_entries, race=race_entries)


def ingest_calendar_dicts(db: Session, entries: list[dict]) -> int:
    """Variante de ingest_calendar qui accepte des dicts."""
    n = 0
    for e in entries:
        name = e.get("name")
        if not name:
            continue
        start_date = e.get("start_date")
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date).date()
            except ValueError:
                start_date = None
        end_date = e.get("end_date")
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date).date()
            except ValueError:
                end_date = None
        year = start_date.year if start_date else datetime.utcnow().year
        t = _upsert_tournament(db, name=name, year=year, surface=e.get("surface"))
        if e.get("category"):
            t.category = e["category"]
        if e.get("city"):
            t.city = e["city"]
        if e.get("country"):
            t.country = e["country"]
        if start_date:
            t.start_date = start_date
        if end_date:
            t.end_date = end_date
        n += 1
    db.commit()
    return n


def ingest_player_bio_dict(db: Session, *, full_name: str, slug: str | None = None,
                           bio: dict) -> bool:
    """Met à jour la bio (Wikipedia) d'un joueur. Retourne True si mis à jour."""
    p = _upsert_player(db, full_name=full_name, slug=slug or slugify(full_name))
    birth_date = bio.get("birth_date")
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.fromisoformat(birth_date).date()
        except ValueError:
            birth_date = None
    if bio.get("wikipedia_url"):
        p.wikipedia_url = bio["wikipedia_url"]
    if birth_date:
        p.birth_date = birth_date
    if bio.get("height_cm"):
        p.height_cm = bio["height_cm"]
    if bio.get("weight_kg"):
        p.weight_kg = bio["weight_kg"]
    if bio.get("hand"):
        p.hand = bio["hand"]
    if bio.get("backhand"):
        p.backhand = bio["backhand"]
    db.commit()
    return True


def ingest_player_matches_dicts(db: Session, *, owner_full_name: str,
                                owner_slug: str | None = None,
                                tennis_abstract_url: str | None = None,
                                matches: list[dict]) -> int:
    """Ingère les matches d'un joueur depuis des dicts (POST GH Actions)."""
    owner = _upsert_player(db, full_name=owner_full_name,
                           slug=owner_slug or slugify(owner_full_name))
    if tennis_abstract_url:
        owner.tennis_abstract_url = tennis_abstract_url
    n = 0
    for m in matches:
        match_date = m.get("match_date")
        if isinstance(match_date, str):
            try:
                match_date = datetime.fromisoformat(match_date).date()
            except ValueError:
                match_date = None
        sm = ScrapedMatch(
            match_date=match_date,
            tournament_name=m.get("tournament_name", ""),
            surface=m.get("surface"),
            round=m.get("round"),
            opponent_name=m.get("opponent_name", ""),
            opponent_rank=m.get("opponent_rank"),
            own_rank=m.get("own_rank"),
            result=m.get("result", ""),
            score=m.get("score"),
            sets_count=m.get("sets_count"),
            duration_minutes=m.get("duration_minutes"),
            stats=m.get("stats") or {},
            source_url=m.get("source_url"),
        )
        if _ingest_match(db, owner=owner, sm=sm):
            n += 1
    db.commit()
    return n
