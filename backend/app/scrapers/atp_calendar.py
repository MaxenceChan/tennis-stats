"""
Scraper calendrier ATP + catégorie de tournoi.

Source principale : https://www.atptour.com/en/tournaments
On scrape la liste des tournois + leur catégorie (ATP 250 / 500 / Masters 1000 / Grand Slam).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup

from app.scrapers.http import fetch

logger = logging.getLogger(__name__)

CALENDAR_URL = "https://www.atptour.com/en/tournaments"


CATEGORY_ALIASES = {
    "grand slam": "Grand Slam",
    "atp masters 1000": "Masters 1000",
    "atp 500": "ATP 500",
    "atp 250": "ATP 250",
    "nitto atp finals": "ATP Finals",
}


@dataclass
class CalendarEntry:
    name: str
    slug: str | None
    city: str | None
    country: str | None
    surface: str | None
    category: str | None
    start_date: date | None
    end_date: date | None


def _normalise_category(txt: str) -> str | None:
    low = txt.lower()
    for key, val in CATEGORY_ALIASES.items():
        if key in low:
            return val
    return None


def _parse_calendar(html: str) -> list[CalendarEntry]:
    soup = BeautifulSoup(html, "lxml")
    out: list[CalendarEntry] = []
    for card in soup.select(".tournament, .tournament-card, .event-item"):
        name_el = card.select_one(".tourney-title, .title, h3")
        if not name_el:
            continue
        name = name_el.get_text(" ", strip=True)
        loc = card.select_one(".tourney-location, .location")
        city = country = None
        if loc:
            loc_txt = loc.get_text(",", strip=True)
            parts = [p.strip() for p in loc_txt.split(",") if p.strip()]
            if parts:
                city = parts[0]
                country = parts[-1] if len(parts) > 1 else None
        cat_el = card.select_one(".tourney-badge, .badge, .category")
        category = _normalise_category(cat_el.get_text(" ", strip=True)) if cat_el else None
        surf_el = card.select_one(".surface, .tourney-surface")
        surface = surf_el.get_text(" ", strip=True) if surf_el else None
        link = card.find("a", href=True)
        slug = None
        if link:
            m = re.search(r"/tournaments/([^/]+)/", link["href"])
            if m:
                slug = m.group(1)
        out.append(
            CalendarEntry(
                name=name, slug=slug, city=city, country=country,
                surface=surface, category=category,
                start_date=None, end_date=None,
            )
        )
    return out


async def fetch_calendar() -> list[CalendarEntry]:
    html = await fetch(CALENDAR_URL)
    return _parse_calendar(html)
