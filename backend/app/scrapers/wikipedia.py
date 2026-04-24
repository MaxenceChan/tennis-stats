"""
Scraper Wikipedia — récupère taille, poids, date de naissance via l'infobox.
On cherche par le nom complet via l'API OpenSearch, puis on parse l'infobox.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from app.scrapers.http import fetch

logger = logging.getLogger(__name__)

WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"


@dataclass
class PlayerBio:
    url: str | None = None
    birth_date: date | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    hand: str | None = None
    backhand: str | None = None


async def _find_article_url(full_name: str) -> str | None:
    # Indirection : on utilise la page HTML de recherche pour rester compatible fetch()
    params = {
        "action": "opensearch",
        "search": f"{full_name} tennis",
        "limit": "1",
        "namespace": "0",
        "format": "xml",
    }
    # opensearch répond en XML si format=xml — on récupère le premier <Url>
    xml = await fetch(WIKI_SEARCH, params=params)
    m = re.search(r"<Url[^>]*>([^<]+)</Url>", xml)
    return m.group(1) if m else None


def _parse_infobox(html: str) -> PlayerBio:
    soup = BeautifulSoup(html, "lxml")
    info = soup.select_one("table.infobox")
    bio = PlayerBio()
    if not info:
        return bio
    for row in info.select("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label = th.get_text(" ", strip=True).lower()
        value = td.get_text(" ", strip=True)
        if "born" in label:
            m = re.search(r"\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2}", value)
            if m:
                try:
                    bio.birth_date = dateparser.parse(m.group()).date()
                except (ValueError, OverflowError):
                    pass
        elif "height" in label:
            m = re.search(r"(\d{3})\s*cm", value.replace("\u00a0", " "))
            if m:
                bio.height_cm = int(m.group(1))
        elif "weight" in label:
            m = re.search(r"(\d{2,3})\s*kg", value.replace("\u00a0", " "))
            if m:
                bio.weight_kg = int(m.group(1))
        elif "plays" in label:
            low = value.lower()
            if "left" in low:
                bio.hand = "L"
            elif "right" in low:
                bio.hand = "R"
            if "two-handed" in low or "two handed" in low:
                bio.backhand = "2"
            elif "one-handed" in low or "one handed" in low:
                bio.backhand = "1"
    return bio


async def fetch_player_bio(full_name: str) -> PlayerBio:
    url = await _find_article_url(full_name)
    if not url:
        return PlayerBio()
    html = await fetch(url)
    bio = _parse_infobox(html)
    bio.url = url
    return bio
