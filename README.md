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

## Déploiement en ligne — 100 % gratuit à vie

| Brique | Service | Limite | Coût |
|---|---|---|---|
| Postgres | **Neon** | 0,5 GB, scale-to-zero | gratuit à vie |
| API FastAPI | **Render** (Web Service free) | sleep après 15 min | gratuit à vie |
| Front statique | **Render** (Static Site free) | 100 GB/mois | gratuit à vie |
| Cron 30 min | **GitHub Actions** (`.github/workflows/refresh.yml`) | illimité (repo public) | gratuit |

> Le sleep de Render est résolu automatiquement : le cron GitHub Actions ping `/health` puis lance l'ingest toutes les 30 min, donc l'API reste réveillée et la base se rafraîchit en boucle.

### Étape 1 — Créer la base Postgres sur Neon

1. https://neon.tech → **Sign up with GitHub** → crée un projet `tennis-stats`, région Europe.
2. Sur le dashboard, copie la **Connection string** (format `postgresql://user:pass@host/db?sslmode=require`).
3. **Important** : remplace `postgresql://` par `postgresql+psycopg://` (driver SQLAlchemy).

### Étape 2 — Déployer sur Render

1. https://render.com → **Sign up with GitHub** → autorise le repo `tennis-stats`.
2. **Dashboard → New + → Blueprint → MaxenceChan/tennis-stats** (branche `main`).
3. Render lit [`render.yaml`](render.yaml) et liste 2 services (api + web). Clique **Apply**.
4. Le 1er build échoue car les secrets ne sont pas encore renseignés — c'est normal.

### Étape 3 — Renseigner les variables d'environnement

#### Sur `tennis-stats-api` → Environment :
- `DATABASE_URL` = la connection string Neon de l'étape 1 (avec `+psycopg`)
- `CORS_ORIGINS` = URL du frontend (ex. `https://tennis-stats-web.onrender.com`)
- `ADMIN_TOKEN` = déjà généré par Render — **copie sa valeur**, tu en auras besoin à l'étape 4

→ Clique **Save Changes** → redéploiement auto.

#### Sur `tennis-stats-web` → Environment :
- `VITE_API_BASE_URL` = `https://tennis-stats-api.onrender.com/api` *(adapte si Render a suffixé le nom)*

→ Clique **Save Changes** → rebuild du front.

### Étape 4 — Configurer le cron GitHub Actions

Sur GitHub : **repo → Settings → Secrets and variables → Actions → New repository secret**, crée 2 secrets :

| Nom | Valeur |
|---|---|
| `API_URL` | `https://tennis-stats-api.onrender.com` *(sans `/api`)* |
| `ADMIN_TOKEN` | la valeur copiée à l'étape 3 |

Le workflow [`refresh.yml`](.github/workflows/refresh.yml) tournera tout seul toutes les 30 min. Pour le déclencher manuellement la 1re fois (peuplement initial) :
**repo → Actions → Refresh data → Run workflow → mode = `full`**.

### C'est tout

- Front public : `https://tennis-stats-web.onrender.com`
- API publique : `https://tennis-stats-api.onrender.com/docs`
- Données rafraîchies automatiquement toutes les 30 min.

### Notes

- Si tu changes le nom des services Render, adapte les URLs dans Settings → Environment.
- Si la 1re requête est lente (~30 s), c'est Neon + Render qui sortent du sleep — les suivantes sont rapides.
- Pour passer en *always-on* sans frais : **Oracle Cloud Free Tier** (4 ARM cores, 24 GB RAM gratuits à vie) — setup Docker compose, plus de boulot mais zéro sleep.

## Notes légales sur le scraping

Tennis Abstract, live-tennis.eu et Wikipedia sont scrapés avec un délai
entre requêtes (`SCRAPE_DELAY_SEC`, 2 s par défaut) et un User-Agent identifiable.
Respectez `robots.txt` et les CGU des sites ; ce projet est à usage personnel/éducatif.
