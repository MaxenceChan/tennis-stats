"""Endpoints d'administration : déclenche manuellement les pipelines.

Tous les endpoints requièrent un bearer token (`Authorization: Bearer <ADMIN_TOKEN>`)
si la variable d'env `ADMIN_TOKEN` est définie. En dev, laissez-la vide.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api._auth import require_admin
from app.database import SessionLocal, get_db
from app.models import Match, Player
from app.schemas.imports import (
    CalendarImport,
    PlayerBioImport,
    PlayerListItem,
    PlayerMatchesImport,
    RankingsImport,
)
from app.services import elo, ingest

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _run_in_session(coro_factory):
    async def runner():
        db = SessionLocal()
        try:
            await coro_factory(db)
        finally:
            db.close()
    return runner


@router.post("/ingest/rankings")
async def ingest_rankings(bg: BackgroundTasks):
    bg.add_task(_run_in_session(ingest.run_rankings_pipeline))
    return {"status": "scheduled"}


@router.post("/ingest/calendar")
async def ingest_calendar(bg: BackgroundTasks):
    bg.add_task(_run_in_session(ingest.run_calendar_pipeline))
    return {"status": "scheduled"}


@router.post("/ingest/bios")
async def ingest_bios(bg: BackgroundTasks, max_players: int = 200):
    async def _run(db: Session):
        await ingest.enrich_player_bios(db, max_players=max_players)
    bg.add_task(_run_in_session(_run))
    return {"status": "scheduled", "max_players": max_players}


@router.post("/ingest/matches")
async def ingest_matches(bg: BackgroundTasks, top_n: int = 100, concurrency: int = 1):
    async def _run(db: Session):
        await ingest.ingest_all_players_matches(db, top_n=top_n, concurrency=concurrency)
    bg.add_task(_run_in_session(_run))
    return {"status": "scheduled", "top_n": top_n}


@router.post("/elo/recompute")
def elo_recompute(db: Session = Depends(get_db)):
    counts = elo.recompute_elo(db)
    return {"status": "done", "counts": counts}


# ---------------------------- IMPORT endpoints (GH Actions push) ---------------

@router.post("/import/rankings")
def import_rankings(payload: RankingsImport, db: Session = Depends(get_db)):
    n = ingest.ingest_rankings_dicts(
        db,
        atp=[r.model_dump() for r in payload.atp],
        race=[r.model_dump() for r in payload.race],
    )
    return {"status": "ok", "ingested": n}


@router.post("/import/calendar")
def import_calendar(payload: CalendarImport, db: Session = Depends(get_db)):
    n = ingest.ingest_calendar_dicts(db, [e.model_dump() for e in payload.entries])
    return {"status": "ok", "ingested": n}


@router.post("/import/player-bio")
def import_player_bio(payload: PlayerBioImport, db: Session = Depends(get_db)):
    bio = payload.model_dump(exclude={"full_name", "slug"})
    ingest.ingest_player_bio_dict(db, full_name=payload.full_name, slug=payload.slug, bio=bio)
    return {"status": "ok"}


@router.post("/import/player-matches")
def import_player_matches(payload: PlayerMatchesImport, db: Session = Depends(get_db)):
    n = ingest.ingest_player_matches_dicts(
        db,
        owner_full_name=payload.owner_full_name,
        owner_slug=payload.owner_slug,
        tennis_abstract_url=payload.tennis_abstract_url,
        matches=[m.model_dump() for m in payload.matches],
    )
    return {"status": "ok", "ingested": n}


@router.get("/players-list", response_model=list[PlayerListItem])
def players_list(
    db: Session = Depends(get_db),
    limit: int = Query(200, ge=1, le=1000),
    missing: str | None = Query(None, description="bio | matches | None"),
):
    """Liste des joueurs ordonnés par classement ATP, optionnellement filtrés
    sur ce qui leur manque (bio Wikipedia ou matches Tennis Abstract)."""
    q = select(Player).order_by(Player.atp_rank.asc().nulls_last()).limit(limit)
    if missing == "bio":
        q = select(Player).where(Player.birth_date.is_(None)).order_by(
            Player.atp_rank.asc().nulls_last()
        ).limit(limit)
    elif missing == "matches":
        q = select(Player).where(Player.tennis_abstract_url.is_(None)).order_by(
            Player.atp_rank.asc().nulls_last()
        ).limit(limit)
    rows = list(db.scalars(q))
    return [
        PlayerListItem(
            id=p.id,
            slug=p.slug,
            full_name=p.full_name,
            atp_rank=p.atp_rank,
            has_bio=p.birth_date is not None,
            has_matches=p.tennis_abstract_url is not None,
        )
        for p in rows
    ]


@router.get("/debug/probe")
async def debug_probe():
    """Test each scraping source and report status codes — useful when the
    deploy IP gets blocked by anti-bot."""
    import httpx

    targets = {
        "live-tennis.eu": "https://live-tennis.eu/en/atp-live-ranking",
        "tennisabstract.com": "https://www.tennisabstract.com/cgi-bin/player.cgi?p=CarlosAlcaraz",
        "wikipedia.org": "https://en.wikipedia.org/wiki/ATP_Rankings",
        "atptour.com": "https://www.atptour.com/en/rankings/singles",
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    results = {}
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for name, url in targets.items():
            try:
                r = await client.get(url, headers=headers)
                results[name] = {"status": r.status_code, "size": len(r.content)}
            except Exception as exc:  # noqa: BLE001
                results[name] = {"error": type(exc).__name__, "msg": str(exc)[:200]}
    return results
