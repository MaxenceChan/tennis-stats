"""
Scraper Tennis Abstract (tennisabstract.com).

Les fiches joueurs ont l'URL : https://www.tennisabstract.com/cgi-bin/player-classic.cgi?p=<SlugNom>
Elles contiennent notamment :
  - Recent Results
  - All Results (lien vers page matches complet)
  - Tour-Level Seasons
  - Recent Titles and Finals
  - Year-End Rankings
  - Major and Recent Events

La structure HTML est largement à base de <table> injectées via JS, mais une version statique
est disponible en paramètre `&table=n`. Ce scraper reste volontairement tolérant : il capture ce
qu'il trouve et laisse les champs manquants à None.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from app.scrapers.http import fetch

logger = logging.getLogger(__name__)

BASE = "https://www.tennisabstract.com"
PLAYER_URL = BASE + "/cgi-bin/player-classic.cgi"


@dataclass
class ScrapedMatch:
    match_date: date | None
    tournament_name: str
    surface: str | None
    round: str | None
    opponent_name: str
    opponent_rank: int | None
    own_rank: int | None
    result: str                 # "W" ou "L"
    score: str | None
    sets_count: int | None
    duration_minutes: int | None
    stats: dict[str, float | None] = field(default_factory=dict)
    source_url: str | None = None


@dataclass
class PlayerProfile:
    slug: str
    matches: list[ScrapedMatch]
    tour_level_seasons: list[dict]
    titles_finals: list[dict]
    year_end_rankings: list[dict]
    major_recent_events: list[dict]


def player_slug_for_url(full_name: str) -> str:
    """Tennis Abstract utilise 'CamelCase' sans espace : 'Carlos Alcaraz' -> 'CarlosAlcaraz'."""
    return re.sub(r"[^A-Za-z]", "", full_name.title())


def _parse_date(txt: str) -> date | None:
    txt = (txt or "").strip()
    if not txt:
        return None
    try:
        return dateparser.parse(txt, default=datetime(2000, 1, 1)).date()
    except (ValueError, OverflowError):
        return None


def _parse_int(txt: str | None) -> int | None:
    if not txt:
        return None
    m = re.search(r"-?\d+", txt.replace(",", ""))
    return int(m.group()) if m else None


def _parse_pct(txt: str | None) -> float | None:
    if not txt:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", txt)
    return float(m.group()) if m else None


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _parse_results_table(table, source_url: str) -> list[ScrapedMatch]:
    """Colonnes attendues (heuristique, tolérant) :
    Date | Tournament | Surface | Rd | Rk | vRk | Opponent | Result | Score | ...
    """
    matches: list[ScrapedMatch] = []
    header_cells = [c.get_text(strip=True).lower() for c in table.select("thead th")] or [
        c.get_text(strip=True).lower() for c in table.select("tr:first-child th, tr:first-child td")
    ]
    idx = {name: i for i, name in enumerate(header_cells)}

    def col(row_cells, *keys):
        for key in keys:
            for name, i in idx.items():
                if key in name and i < len(row_cells):
                    return row_cells[i]
        return None

    body_rows = table.select("tbody tr") or table.select("tr")[1:]
    for tr in body_rows:
        cells = tr.find_all("td")
        if len(cells) < 5:
            continue
        date_txt = _text(col(cells, "date"))
        tourney = _text(col(cells, "tournament", "tourney"))
        surface = _text(col(cells, "surface")) or None
        rd = _text(col(cells, "rd", "round")) or None
        own_rank = _parse_int(_text(col(cells, "rk")))
        opp_rank = _parse_int(_text(col(cells, "vrk", "opp rank")))
        opp_name = _text(col(cells, "opponent", "vs"))
        result = _text(col(cells, "result", "w/l"))[:1].upper() or ""
        score = _text(col(cells, "score")) or None
        duration = _parse_int(_text(col(cells, "time", "duration")))

        stats = {
            "ace_pct": _parse_pct(_text(col(cells, "ace%", "a%"))),
            "double_fault_pct": _parse_pct(_text(col(cells, "df%"))),
            "first_serve_pct": _parse_pct(_text(col(cells, "1st in", "1stin", "1%"))),
            "first_serve_win_pct": _parse_pct(_text(col(cells, "1st%", "1stwon"))),
            "second_serve_win_pct": _parse_pct(_text(col(cells, "2nd%", "2ndwon"))),
            "break_points_saved": _parse_pct(_text(col(cells, "bpsvd", "bp saved"))),
            "dominance_ratio": _parse_pct(_text(col(cells, "dr", "dom"))),
        }
        sets_count = None
        if score:
            sets_count = len([s for s in re.split(r"\s+", score) if re.match(r"\d+-\d+", s)])

        matches.append(
            ScrapedMatch(
                match_date=_parse_date(date_txt),
                tournament_name=tourney,
                surface=surface,
                round=rd,
                opponent_name=opp_name,
                opponent_rank=opp_rank,
                own_rank=own_rank,
                result=result if result in ("W", "L") else "",
                score=score,
                sets_count=sets_count,
                duration_minutes=duration,
                stats=stats,
                source_url=source_url,
            )
        )
    return matches


def _parse_simple_kv_table(table) -> list[dict]:
    """Transforme une table en liste de dicts {header: value}."""
    headers = [h.get_text(strip=True) for h in table.select("thead th")]
    if not headers:
        first = table.find("tr")
        headers = [c.get_text(strip=True) for c in first.find_all(["th", "td"])] if first else []
    rows: list[dict] = []
    for tr in (table.select("tbody tr") or table.select("tr")[1:]):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
        if not cells:
            continue
        rows.append({headers[i] if i < len(headers) else f"col{i}": v for i, v in enumerate(cells)})
    return rows


async def fetch_player_profile(slug: str) -> PlayerProfile:
    """Récupère la fiche joueur complète."""
    url = f"{PLAYER_URL}?p={slug}"
    html = await fetch(url)
    soup = BeautifulSoup(html, "lxml")

    matches: list[ScrapedMatch] = []
    seasons: list[dict] = []
    titles: list[dict] = []
    year_end: list[dict] = []
    events: list[dict] = []

    for table in soup.select("table"):
        section = ""
        prev = table.find_previous(["h2", "h3", "h4", "b", "strong"])
        if prev:
            section = prev.get_text(" ", strip=True).lower()

        if "result" in section:
            matches.extend(_parse_results_table(table, source_url=url))
        elif "season" in section:
            seasons.extend(_parse_simple_kv_table(table))
        elif "title" in section or "final" in section:
            titles.extend(_parse_simple_kv_table(table))
        elif "year-end" in section or "year end" in section:
            year_end.extend(_parse_simple_kv_table(table))
        elif "event" in section or "major" in section:
            events.extend(_parse_simple_kv_table(table))

    return PlayerProfile(
        slug=slug,
        matches=matches,
        tour_level_seasons=seasons,
        titles_finals=titles,
        year_end_rankings=year_end,
        major_recent_events=events,
    )
