# MealRoulette

MealRoulette is a self-hosted household meal planning app for deciding what to eat, planning lunch and dinner, generating shopping lists, sending Telegram reminders, and cooking from structured recipe steps.

**v0.1 foundation** is implemented: auth, catalog API, and a dish library UI (login, dish cards, dish/recipe CRUD, ingredients, steps, tags, seasonality). Meal planning, shopping lists, Telegram, and the scheduler are not built yet — see [docs/BACKLOG.md](docs/BACKLOG.md).

## Documentation

- [Full specification](SPECS.md)
- [Cursor implementation roadmap](docs/CURSOR_ROADMAP.md)
- [MVP scope](docs/MVP.md)
- [Development backlog and progress](docs/BACKLOG.md)
- [Releases and git tags](docs/RELEASES.md) — product version tags (`v0.1.0`, …)
- [CodeRabbit PR reviews](docs/CODERABBIT.md) — manual `@coderabbitai review` after CI is green

## Target Stack

- Backend: Python 3.12+, FastAPI, Pydantic, SQLAlchemy, Alembic
- Database: PostgreSQL
- Worker: APScheduler
- Frontend: React + Vite
- Deployment: Docker Compose, suitable for Raspberry Pi

## Target Services

```text
api       FastAPI backend
worker    APScheduler jobs for Telegram reminders and backups
frontend  Responsive web UI
db        PostgreSQL
```

## Initial Development Flow

Use the roadmap as the implementation guide:

1. Read `SPECS.md`.
2. Follow `docs/CURSOR_ROADMAP.md` phase by phase.
3. Track progress in `docs/BACKLOG.md`.
4. Keep schema migrations, unit tests, integration tests, pre-commit checks, and Docker Compose working at each phase.

## Developer Commands

```bash
cp .env.example .env
make free-ports    # stop containers using ports 3000, 8000, 5432
make up            # free ports, then start the stack
make test
```

`make up` and `make test` already call `make free-ports` first. Run it manually if you start Docker Compose directly.

Backend only:

```bash
cd backend
pip install ".[dev]"
pytest
alembic upgrade head
```

Frontend only:

```bash
cd frontend
npm install
npm run dev
npm test -- --run
```

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Integration tests expect PostgreSQL at `TEST_DATABASE_URL`. The easiest local setup is `docker compose up db`.

## Database migrations (Alembic)

When the app data model changes (new tables like `users`, `dishes`, etc.), the PostgreSQL schema must be updated too.

**Alembic** is the tool that applies those schema changes safely, step by step, using versioned migration files in `backend/alembic/versions/`.

- `001_initial` — bootstrap
- `002_users` — users and refresh tokens
- `003_catalog` — dishes, recipes, ingredients, units, tags
- `004_seed_units_tags` — no-op (seed moved to startup CLI)
- `005_recipe_difficulty` — recipe difficulty
- `006_dish_classification` — dish course, status, planning fields
- `007_dish_recipe_ownership` — dish defaults vs recipe overrides, recipe type
- `008_recipe_is_main` — main recipe flag per dish
- `009_dish_image_url` — optional dish image URL
- `010_dish_course_simplify` — course limited to starter, main, dessert
- `011_meal_planning` — meal plans, plan items, ratings

With Docker Compose, the **API container runs migrations automatically** on startup (`alembic upgrade head`), then loads **reference catalog data** (standard units and starter tags) from YAML if those rows are not already present.

Local development without Docker:

```bash
cd backend
alembic upgrade head
python -m mealroulette.commands.seed_reference_data
```

Reference data lives in `backend/mealroulette/data/reference/` (`units.yaml`, `tags.yaml`). The loader is idempotent: re-running it only inserts missing rows, so it is safe after upgrades or when adding new defaults to the YAML files.

Unit compatibility and aggregation rules (when to merge g + kg, when to keep "2 onions" and "200 g onion" separate) live in `mealroulette.services.quantities`. Shopping lists and exports must use that module — see SPECS §9.

Bootstrap the first admin user once (after the stack is up). Omit `--password` to be prompted securely:

```bash
docker exec -it mealroulette-api python -m mealroulette.commands.bootstrap_admin \
  --username admin --email admin@example.com
```

## Trying the API

After `make up`:

| Service | URL |
| --- | --- |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |
| Frontend | http://localhost:3000 |

### Login flow in Swagger (`/docs`)

The API uses **two different tokens**. Mixing them up returns `401 Unauthorized`.

| Token | Used for |
| --- | --- |
| `access_token` | `GET /api/auth/me`, `GET /api/users`, and other protected endpoints |
| `refresh_token` | `POST /api/auth/refresh` and `POST /api/auth/logout` only |

**Easiest way (Swagger Authorize):**

1. Open http://localhost:8000/docs
2. Click **Authorize** (top right)
3. Enter your **username** and **password** (leave client id/secret empty)
4. Click **Authorize**, then **Close**
5. Call any protected endpoint — Swagger sends the `access_token` automatically

`POST /api/auth/login` still works for manual testing, but it does **not** attach the token to other requests. Use **Authorize** or `POST /api/auth/token` instead.

**Manual token paste (alternative):**

1. Call `POST /api/auth/login` and copy `access_token`
2. Click **Authorize** and paste only the token (no `Bearer ` prefix)

**Refresh token:**

1. Call `POST /api/auth/login` (or use a saved `refresh_token`)
2. Call `POST /api/auth/refresh` with the **refresh** token in the body:

```json
{
  "refresh_token": "paste-refresh-token-here"
}
```

Each successful refresh **replaces** the refresh token. Reusing the old one returns `401`.

Do **not** put the refresh token in **Authorize** — that field is only for the access token.

**Common mistakes**

| Mistake | Error |
| --- | --- |
| Calling protected endpoints without **Authorize** | `Not authenticated` |
| Putting `refresh_token` in Authorize | `Invalid token type` |
| Putting `access_token` in `/api/auth/refresh` body | `Invalid token type` |
| Reusing a refresh token after `/refresh` or `/logout` | `Refresh token revoked or expired` |

### curl example

```bash
# Login (use the password you chose during bootstrap)
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}'

# Me (replace TOKEN with access_token from login)
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Suggested Cursor Prompt

```text
Read SPECS.md and docs/CURSOR_ROADMAP.md.

Implement Phase 0 and Phase 1 only:
- FastAPI backend with /health
- SQLAlchemy 2.x database setup
- Alembic setup
- PostgreSQL connection through DATABASE_URL
- Docker Compose with api, worker placeholder, frontend placeholder, and db
- React + Vite frontend shell that can display API health status
- .env.example
- basic backend unit and integration tests
- pre-commit hook and CI workflow that run tests on commit and push

Do not implement domain models yet except what is necessary for Alembic/bootstrap.
Keep the repository structure aligned with docs/CURSOR_ROADMAP.md.
```

## Product Summary

MealRoulette is an API-first, Dockerized FastAPI/PostgreSQL application with a responsive frontend, APScheduler worker, Telegram reminder integration, structured recipe data, ingredient normalization, tag-based classification, and an explainable rule-based meal scheduler.
