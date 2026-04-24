"""
Script appelé par le cron Render (ou tout autre cron) pour rafraîchir les données.

Utilisation :
  python -m app.tasks.refresh rankings    # rapide (~10 s) — toutes les 30 min
  python -m app.tasks.refresh full        # complet — quotidien
"""
from __future__ import annotations

import asyncio
import logging
import sys

from app.database import SessionLocal
from app.services import elo, ingest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
logger = logging.getLogger("refresh")


async def _rankings() -> None:
    db = SessionLocal()
    try:
        n = await ingest.run_rankings_pipeline(db)
        logger.info("rankings: %d players upserted", n)
    finally:
        db.close()


async def _full() -> None:
    db = SessionLocal()
    try:
        logger.info("step 1/4 rankings")
        await ingest.run_rankings_pipeline(db)

        logger.info("step 2/4 calendar")
        try:
            await ingest.run_calendar_pipeline(db)
        except Exception as exc:
            logger.warning("calendar failed: %s", exc)

        logger.info("step 3/4 bios (top 200)")
        await ingest.enrich_player_bios(db, max_players=200)

        logger.info("step 4/4 matches (top 200, concurrency=1)")
        await ingest.ingest_all_players_matches(db, top_n=200, concurrency=1)

        logger.info("recompute elo")
        elo.recompute_elo(db)
    finally:
        db.close()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "rankings"
    if mode == "rankings":
        asyncio.run(_rankings())
    elif mode == "full":
        asyncio.run(_full())
    else:
        print(f"Unknown mode: {mode}. Use 'rankings' or 'full'.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
