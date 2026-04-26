from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import calendar as calendar_api
from app.api import players as players_api
from app.api import rankings as rankings_api
from app.api import admin as admin_api
from app.api import live as live_api
from app.config import get_settings
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Tennis Stats API",
    version="0.1.0",
    description="API REST pour classements ATP/Race/Elo, calendrier, fiches joueurs.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

api_prefix = "/api"
app.include_router(rankings_api.router, prefix=api_prefix)
app.include_router(players_api.router, prefix=api_prefix)
app.include_router(calendar_api.router, prefix=api_prefix)
app.include_router(admin_api.router, prefix=api_prefix)
app.include_router(live_api.router, prefix=api_prefix)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
