# Tennis Stats

Plateforme de statistiques ATP inspirée de Tennis Abstract : classements (ATP Live, Race, Elo), calendrier, fiches joueurs détaillées.

## Architecture

```
tennis-stats/
├── backend/           # FastAPI + SQLAlchemy + scrapers (Python 3.11)
│   ├── app/
│   │   ├── api/        # Routes REST (players, rankings, matches, tournaments, calendar)
│   │   ├── models/     # Modèles SQLAlchemy (Player, Match, Tournament)
│   │   ├── schemas/    # Schémas Pydantic
│   │   ├── scrapers/   # live-tennis.eu, Tennis Abstract, Wikipedia, ATP calendar
│   │   ├── services/   # Logique métier (Elo, ingestion)
│   │   └── tasks/      # Tâches planifiées (APScheduler)
│   └── alembic/        # Migrations
├── frontend/           # React + Vite + TypeScript + React Router
│   └── src/
│       ├── api/        # Client HTTP
│       ├── components/ # Header, PlayerSearch, tableaux de stats
│       └── pages/      # Home, Rankings, Calendar, PlayerSearch, PlayerDetail
├── docker-compose.yml  # Postgres + backend + frontend
└── .github/workflows/  # CI (lint + tests)
```

## Sources de données

| Table | Source | Fréquence |
|-------|--------|-----------|
| `players` (liste + rank ATP + rank Race) | live-tennis.eu | Quotidienne |
| `players` (taille, poids, âge) | Wikipedia | Hebdomadaire |
| `matches` + stats détaillées | Tennis Abstract (par joueur) | Quotidienne |
| `tournaments` (nom, surface) | Tennis Abstract | Avec matches |
| `tournaments.category` (ATP 250/500/1000/GC) | ATP Tour / Wikipedia | Au besoin |
| Rangs Elo | Calculé à partir de `matches` | Recalculé après ingestion |

## Démarrage rapide

### Option Docker (recommandé)

```bash
cp .env.example .env
docker compose up --build
# Backend : http://localhost:8000/docs
# Frontend : http://localhost:5173
```

### Développement local

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # (Git Bash) ou .venv\Scripts\activate (cmd)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Peuplement initial

```bash
cd backend
python -m app.tasks.bootstrap   # scrape les 1000 joueurs + leurs matches
```

Le bootstrap complet peut durer plusieurs heures (rate-limit sur Tennis Abstract).
Lancez-le au besoin, ou laissez le scheduler tourner en fond.

## Endpoints principaux

- `GET /api/rankings/atp` — classement ATP Live
- `GET /api/rankings/race` — classement ATP Race
- `GET /api/rankings/elo` — classement Elo calculé
- `GET /api/players/search?q=<query>`
- `GET /api/players/{id}` — fiche complète (recent, all-results, seasons, titres, year-end, events)
- `GET /api/calendar` — calendrier ATP
- `POST /api/admin/ingest/{source}` — déclenche un scraping manuel

Voir `/docs` (OpenAPI) pour la liste exhaustive.

## Notes légales sur le scraping

Tennis Abstract, live-tennis.eu et Wikipedia sont scrapés avec un délai
entre requêtes (`SCRAPE_DELAY_SEC`, 2 s par défaut) et un User-Agent identifiable.
Respectez `robots.txt` et les CGU des sites ; ce projet est à usage personnel/éducatif.
