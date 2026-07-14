# MealRoulette

Self-hosted household meal planning: dishes and recipes, weekly lunch/dinner plans, shopping lists, Telegram reminders, explainable scheduling, cooking mode, and JSON backup/restore.

Current release: **v0.8.0** — see [docs/releases/v0.8.0.md](docs/releases/v0.8.0.md).

## Documentation

**Start here:** [docs/README.md](docs/README.md) — authority map (product spec, features, operations, status).

| Doc | Purpose |
| --- | --- |
| [SPECS.md](SPECS.md) | Product source of truth |
| [docs/BACKLOG.md](docs/BACKLOG.md) | Current status and progress |
| [docs/CURSOR_ROADMAP.md](docs/CURSOR_ROADMAP.md) | Implementation phases |

## Stack

Python 3.12 · FastAPI · PostgreSQL · React + Vite · Docker Compose · APScheduler worker

## Quick start

```bash
cp .env.example .env
make up          # free ports, start api + worker + frontend + db
make test        # backend + frontend tests
```

The API container runs `alembic upgrade head` on startup. Migration files live in `backend/alembic/versions/` (current head: check with `alembic heads`).

Bootstrap the first admin user:

```bash
docker exec -it mealroulette-api python -m mealroulette.commands.bootstrap_admin \
  --username admin --email admin@example.com
```

Load development catalog data (idempotent):

```bash
docker exec -it mealroulette-api python -m mealroulette.commands.import_ingredient_seed
docker exec -it mealroulette-api python -m mealroulette.commands.import_sample_dishes
```

Ingredient taxonomy YAML: `backend/mealroulette/data/taxonomy/`. Canonical seed: `backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml`. See [docs/taxonomy/README.md](docs/taxonomy/README.md).

## URLs (local)

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

## Developer commands

```bash
make free-ports   # if ports 3000/8000/5432 are busy
make test-backend
make test-backend TESTS="tests/test_import_ingredients.py tests/test_import_dishes.py"
make test-frontend
make test-frontend FRONTEND_TESTS="src/features/planning/planFormat.test.ts"
cd backend && alembic upgrade head && pytest
cd frontend && npm run dev
```

Integration tests use PostgreSQL `mealroulette_test` — `make test-db-setup` from the repo root.

Telegram, scheduler, and backup operations are documented under [docs/features/](docs/features/) and [docs/operations/](docs/operations/).
