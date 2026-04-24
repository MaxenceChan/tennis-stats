"""Tests offline des parseurs HTML — pas d'appel réseau."""
from app.scrapers.live_tennis import _parse_ranking
from app.scrapers.wikipedia import _parse_infobox


LIVE_HTML = """
<html><body><table>
  <tr><th>R</th><th>C</th><th>Player</th><th>Pts</th></tr>
  <tr><td>1</td><td>ESP</td><td><a href="/p/alcaraz">Carlos Alcaraz</a></td><td>11,540</td></tr>
  <tr><td>2</td><td>ITA</td><td><a href="/p/sinner">Jannik Sinner</a></td><td>10,200</td></tr>
</table></body></html>
"""


def test_parse_ranking():
    rows = _parse_ranking(LIVE_HTML, limit=10)
    assert len(rows) == 2
    assert rows[0].rank == 1
    assert rows[0].player_name == "Carlos Alcaraz"
    assert rows[0].country == "ESP"
    assert rows[0].points == 11540


WIKI_HTML = """
<table class="infobox">
  <tr><th>Born</th><td>5 May 2003</td></tr>
  <tr><th>Height</th><td>183 cm</td></tr>
  <tr><th>Weight</th><td>74 kg</td></tr>
  <tr><th>Plays</th><td>Right-handed (two-handed backhand)</td></tr>
</table>
"""


def test_parse_infobox():
    bio = _parse_infobox(WIKI_HTML)
    assert bio.height_cm == 183
    assert bio.weight_kg == 74
    assert bio.hand == "R"
    assert bio.backhand == "2"
    assert bio.birth_date is not None
    assert bio.birth_date.year == 2003
