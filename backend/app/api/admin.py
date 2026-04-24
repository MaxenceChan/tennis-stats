"""Endpoints d'administration : déclenche manuellement les pipelines."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.services import elo, ingest

router = APIRouter(prefix="/admin", tags=["admin"])


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
