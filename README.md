# MealRoulette

MealRoulette is a self-hosted household meal planning app for deciding what to eat, planning lunch and dinner, generating shopping lists, sending Telegram reminders, and cooking from structured recipe steps.

**v0.5.0** adds the explainable meal scheduler: generate week, reroll, undo, family-vector similarity, selection reasons, scheduled Friday roulette, and Telegram “New roulette”. See [docs/releases/v0.5.0.md](docs/releases/v0.5.0.md) and [docs/SCHEDULER.md](docs/SCHEDULER.md).

## Documentation

- [Full specification](SPECS.md)
- [Cursor implementation roadmap](docs/CURSOR_ROADMAP.md)
- [MVP scope](docs/MVP.md)
- [Development backlog and progress](docs/BACKLOG.md)
- [Releases and git tags](docs/RELEASES.md) — product version tags (`v0.1.0`, `v0.2.0`, …)
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
worker    APScheduler jobs for Telegram reminders, scheduled roulette, and backups
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

Integration tests expect PostgreSQL at `TEST_DATABASE_URL` (default: `mealroulette_test` on `localhost:5432`). From the **repository root**:

```bash
make test-db-setup   # starts db, creates mealroulette_test if needed
cd backend && python -m pytest -q
```

Or run everything in one step: `make test-backend`.

If you only run `docker compose up -d db`, ensure Docker/Colima is running and the `db` service is healthy (`docker compose ps`). The init script creates `mealroulette_test` on first volume init; for an existing Postgres volume use `make test-db-setup` once.

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
- `012_meal_item_eaten_status` — eaten/ate_leftovers statuses, is_locked, skip_comment
- `013_meal_ratings_dish_id` — meal_ratings table (replaces ratings)
- `014_review_saved_at` — review_saved_at on meal plan items
- `015_shopping_lists` — shopping lists and shopping list items
- `016_shopping_contributions` — per-meal ingredient breakdown on list items
- `017_ingredient_unit_behavior` — ingredient families, shopping units, conversion approval
- `018_ingredient_conversion_unique` — unique constraint on ingredient conversion triplets
- `019_telegram_settings` — Telegram reminder settings and subscribers

With Docker Compose, the **API container runs migrations automatically** on startup (`alembic upgrade head`), then loads **reference catalog data** (standard units and starter tags) from YAML if those rows are not already present.

Local development without Docker:

```bash
cd backend
alembic upgrade head
python -m mealroulette.commands.seed_reference_data
```

Reference data lives in `backend/mealroulette/data/reference/` (`units.yaml`, `tags.yaml`). Ingredient unit conversions are defined in `backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml` (the legacy `reference/ingredient_conversions.yaml` is deprecated). The loaders are idempotent: re-running them only inserts missing rows, so it is safe after upgrades or when adding new defaults to the YAML files.

Unit compatibility and aggregation rules (when to merge g + kg, when to keep "2 onions" and "200 g onion" separate, when to use approved ingredient conversions) live in `mealroulette.services.quantities`. Shopping lists and exports must use that module — see SPECS §9.

Bootstrap the first admin user once (after the stack is up). Omit `--password` to be prompted securely:

```bash
docker exec -it mealroulette-api python -m mealroulette.commands.bootstrap_admin \
  --username admin --email admin@example.com
```

Load catalog data for development (idempotent — run in this order):

```bash
# 1. Canonical ingredients, aliases, and unit conversions
docker exec -it mealroulette-api python -m mealroulette.commands.import_ingredient_seed

# 2. Sample dishes and recipes (requires ingredients from step 1)
docker exec -it mealroulette-api python -m mealroulette.commands.import_sample_dishes
```

Without Docker, from `backend/` after `alembic upgrade head` and `seed_reference_data`:

```bash
python -m mealroulette.commands.import_ingredient_seed
python -m mealroulette.commands.import_sample_dishes
```

**Ingredient seed:** `backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml`. Use `--no-bootstrap-approve` to import conversion suggestions without auto-approving them for shopping aggregation.

**Dish fixtures:** `backend/mealroulette/data/fixtures/sample_dishes.yaml` (inside the container: `/app/mealroulette/data/fixtures/sample_dishes.yaml`). Use `--file` only with a path that exists **inside the container**, or omit `--file` for the default. After editing fixtures locally, rebuild the API image: `docker compose up -d --build api`.

### Telegram

MealRoulette uses a Telegram bot for household reminders and on-demand meal/shopping messages. The **worker** polls bot commands and sends the daily reminder; the **API** exposes admin settings and manual send endpoints.

#### Quick start

1. Create a bot with [@BotFather](https://t.me/BotFather) and add to `.env`:

   ```bash
   TELEGRAM_BOT_TOKEN=your-token-here
   TELEGRAM_BOT_USERNAME=your_bot_username   # optional, see below
   ```

2. Restart **api** and **worker**:

   ```bash
   docker compose up -d --build api worker
   ```

3. In Telegram, message your bot: **`/subscribe`**
4. As admin, open **Telegram** in the app header (`/settings/telegram`), enable reminders, and use **Send test**.

**Security note:** anyone who discovers your bot can `/subscribe` today. A pairing code may be added later.

#### Environment variables

| Variable | Required | Used by | Description |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes (for bot features) | `api`, `worker` | Bot token from BotFather. Not stored in the database. |
| `TELEGRAM_BOT_USERNAME` | No | `api`, `worker` | Bot username **without** `@`. Enables clickable dish links in HTML planning/reminder messages (`t.me/username?start=recipe_<id>`). If omitted, the worker tries to resolve it via Telegram `getMe`. |

Without `TELEGRAM_BOT_TOKEN`, bot commands and reminders are disabled (the worker logs a warning).

#### Admin settings (database)

Configured at **`/settings/telegram`** or `PUT /api/telegram/settings`. Read-only fields come from `GET /api/telegram/settings`.

| Setting | Type | Default | What it does |
| --- | --- | --- | --- |
| `enabled` | bool | `false` | When `true`, the worker may send the daily reminder and **Send reminder now** is allowed. |
| `daily_reminder_time` | time | `08:00` | Local time (see `timezone`) to send the daily reminder once per day. |
| `timezone` | string | `Europe/Paris` | IANA timezone for `daily_reminder_time` and on-demand date windows. |
| `shopping_window_days` | int (1–14) | `3` | Length of the reminder window. Daily job and **Send reminder now** send the same HTML as **`/reminder N`**. |
| `group_by_category` | bool | `true` | Group ingredients by category when sending a **saved shopping list** via `POST /api/shopping-lists/{id}/send-telegram` (plain text). Does not affect `/reminder` or the daily job. |
| `has_bot_token` | bool | — | Read-only: whether `TELEGRAM_BOT_TOKEN` is set in the environment. |
| `subscriber_count` | int | — | Read-only: number of chats that sent `/subscribe`. |
| `last_sent_at` | datetime | — | Read-only: last successful broadcast to subscribers. |
| `last_error` | string | — | Read-only: last send failure message, if any. |

`include_today` and `include_pantry_items` remain in the API schema for compatibility but are **not used** in v0.4 — the daily reminder and `/reminder` always use today → N−1 days in `timezone` with pantry items included.

Subscribers are stored separately (`GET /api/telegram/subscribers`). Each person must **`/subscribe`** in Telegram; there is no fixed chat ID in settings.

#### Bot commands

All commands are handled by the worker via long polling. On-demand messages use **HTML** unless noted.

| Command | Description |
| --- | --- |
| `/subscribe` or `/start` | Join the reminder list (broadcast target for daily job). |
| `/unsubscribe` or `/stop` | Leave the reminder list. |
| `/planning [days]` | Meal plan for the next `days` (default **3**, max **14**). Shows lunch/dinner, prep/cook times, dish names as links when `TELEGRAM_BOT_USERNAME` is set. |
| `/reminder [days]` | Same window as `/planning`, plus **Ingredients list:** with per-dish breakdown. Pantry items included. |
| `/shopping [days]` | Category-grouped shopping totals only (no per-meal breakdown). Pantry items included. |
| `/start recipe_<id>` | Open full recipe (ingredients + steps). Used when tapping a dish link in planning/reminder. |
| `/recipe <id>` | Same as above, by recipe id (fallback). |
| `/help` | Command summary. |

On-demand windows always start **today** in the household `timezone` and run through the next `days − 1` calendar days.

#### Scheduled vs manual sends

| Trigger | Message | Format |
| --- | --- | --- |
| Daily job (worker, at `daily_reminder_time`) | Same as **`/reminder`** with `shopping_window_days` | HTML |
| **Send reminder now** (admin UI / `POST /api/telegram/send-daily-reminder`) | Same as daily job | HTML |
| **Send test** (`POST /api/telegram/test`) | Short connectivity check | Plain text |
| Saved shopping list (`POST /api/shopping-lists/{id}/send-telegram`) | Shopping list for that saved list | Plain text; respects `group_by_category` |

Broadcasts go to **all subscribers**, not only the admin.

#### Admin API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/telegram/settings` | Read settings (no secrets). |
| `PUT` | `/api/telegram/settings` | Update schedule and flags. |
| `GET` | `/api/telegram/subscribers` | List subscribed chats. |
| `POST` | `/api/telegram/test` | Send test message. |
| `POST` | `/api/telegram/send-daily-reminder` | Send reminder now (same as daily job). |
| `POST` | `/api/shopping-lists/{id}/send-telegram` | Send a saved shopping list. |

All Telegram admin routes require an **admin** JWT.

### Scheduler (automatic roulette)

The **worker** also runs the scheduled weekly roulette when enabled. The **API** exposes scheduler settings and a manual run endpoint.

#### Quick start

1. As admin, open **Settings** (mobile: **More** tab) → **Weekly targets** for fish/meat/pasta counts, or **Auto roulette** (`/settings/scheduler`).
2. Enable the job, set weekday/time/timezone (default Friday 18:00), and `target_week_offset` (default `1` = next Mon–Sun).
3. Use **Run now** to test, or wait for the worker cron (same minute poll as Telegram reminders).
4. Optionally enable **Notify Telegram** to broadcast a **“New roulette”** HTML plan to subscribers after a successful generate.

#### Admin settings (database)

| Setting | Type | Default | What it does |
| --- | --- | --- | --- |
| `enabled` | bool | `false` | When `true`, worker may run on schedule and **Run now** is allowed. |
| `run_weekday` | int (0–6) | `4` | Local weekday to trigger (0 = Monday, 4 = Friday). |
| `run_time` | time | `18:00` | Local time in `timezone`. |
| `timezone` | string | `Europe/Paris` | IANA timezone for schedule. |
| `target_week_offset` | int | `1` | Which Mon–Sun week to fill (`0` = current week, `1` = next week). |
| `notify_telegram` | bool | `true` | Send “New roulette” to subscribers after generate. |
| `notify_planning_days` | int (1–14) | `7` | Days of plan shown in the Telegram message. |
| `last_roulette_at` | datetime | — | Read-only: last successful scheduled/manual run. |
| `last_error` | string | — | Read-only: last failure message, if any. |

#### Plan UI roulette

On **Plan** (`/plan`): **Generate week** fills unlocked slots; **Reroll** one meal; **Undo** last action; **Swap** two slots; locked and manual picks are preserved. Selection reasons appear on auto-picked meals.

#### Scheduler admin API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/scheduler/settings` | Read scheduler settings. |
| `PUT` | `/api/scheduler/settings` | Update schedule and notify flags. |
| `POST` | `/api/scheduler/run-roulette` | Run generate now (ignores weekday/time). |

Roulette endpoints (`POST /api/meal-plans/{id}/generate`, reroll, undo, swap, assign) require a normal user JWT. Full API behaviour: [docs/SCHEDULER.md](docs/SCHEDULER.md).

## Trying the API

After `make up`:

| Service | URL |
| --- | --- |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |
| Frontend | http://localhost:3000 |

On a phone or another device on the same Wi‑Fi, open `http://<this-computer-ip>:3000` — no `VITE_API_URL` or IP config needed; the UI calls `/api` on the same host and Vite proxies to the backend.

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
2. Click **Authorize** and paste only the token (no `Bearer` prefix)

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
