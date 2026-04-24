"""
Peuplement initial : à lancer une fois après les migrations.

  python -m app.tasks.bootstrap
"""
from __future__ import annotations

import asyncio
import logging

from app.database import SessionLocal
from app.services import elo, ingest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
logger = logging.getLogger("bootstrap")


async def main() -> None:
    db = SessionLocal()
    try:
        logger.info("Step 1/4 — Rankings (live-tennis)")
        await ingest.run_rankings_pipeline(db)

        logger.info("Step 2/4 — Calendar (atptour.com)")
        try:
            await ingest.run_calendar_pipeline(db)
        except Exception as exc:
            logger.warning("Calendar pipeline failed: %s", exc)

        logger.info("Step 3/4 — Player bios (Wikipedia)")
        await ingest.enrich_player_bios(db, max_players=300)

        logger.info("Step 4/4 — Player matches (Tennis Abstract, top 100)")
        await ingest.ingest_all_players_matches(db, top_n=100, concurrency=1)

        logger.info("Step 5/4 — Recompute Elo")
        elo.recompute_elo(db)
    finally:
        db.close()
    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
