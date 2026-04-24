"""
Scraper pour live-tennis.eu — classement ATP Live et ATP Race Live.

Les pages visées (structure HTML simple, tables numérotées) :
 - https://live-tennis.eu/en/atp-live-ranking
 - https://live-tennis.eu/en/atp-race-live-ranking
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.scrapers.http import fetch

logger = logging.getLogger(__name__)

ATP_LIVE_URL = "https://live-tennis.eu/en/atp-live-ranking"
ATP_RACE_URL = "https://live-tennis.eu/en/atp-race-live-ranking"


@dataclass
class RankingEntry:
    rank: int
    player_name: str
    country: str | None
    points: int | None
    player_href: str | None


def _parse_ranking(html: str, limit: int = 1000) -> list[RankingEntry]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[RankingEntry] = []
    # live-tennis rend une grande <table>. On prend toutes les <tr>.
    for tr in soup.select("table tr"):
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue
        # col 0 = rank, col 1 = pays/flag, col 2 = nom (avec <a>), dernière col = pts
        rank_txt = cells[0].get_text(strip=True)
        if not rank_txt.isdigit():
            continue
        rank = int(rank_txt)
        country = cells[1].get_text(strip=True) or None
        name_cell = cells[2]
        a = name_cell.find("a")
        name = (a.get_text(strip=True) if a else name_cell.get_text(strip=True)).strip()
        href = a.get("href") if a else None
        points_txt = cells[-1].get_text(strip=True).replace(",", "").replace(" ", "")
        pts = int(points_txt) if points_txt.isdigit() else None
        rows.append(RankingEntry(rank=rank, player_name=name, country=country, points=pts, player_href=href))
        if rank >= limit:
            break
    return rows


async def fetch_atp_live(limit: int = 1000) -> list[RankingEntry]:
    html = await fetch(ATP_LIVE_URL)
    return _parse_ranking(html, limit=limit)


async def fetch_atp_race(limit: int = 1000) -> list[RankingEntry]:
    html = await fetch(ATP_RACE_URL)
    return _parse_ranking(html, limit=limit)


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s
