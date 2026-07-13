# MealRoulette - Cursor Implementation Roadmap

This roadmap is the architectural boilerplate for implementing MealRoulette in Cursor. Treat `SPECS.md` as the product source of truth and this file as the build sequence.

## Guiding Constraints

- Build API-first. Every frontend feature should map to a documented backend endpoint.
- Keep the data model normalized from the first migration. Ingredient cleanup later will be expensive.
- Prefer boring, testable service objects over hidden magic.
- Every phase must ship with unit tests for services and integration tests for the API endpoints introduced in that phase.
- Commits must not bypass the automated test gate unless explicitly documented as an emergency exception.
- Do not use embeddings, vector databases, online scraping, nutrition tracking, or complex optimization algorithms in v1.
- LLM output is always draft data and must go through user confirmation before persistence.
- All write endpoints must require authentication.
- Secrets such as Telegram bot tokens must never be returned in normal API responses.
- The app must run locally with Docker Compose and be suitable for Raspberry Pi deployment.

## Recommended Repository Layout

```text
mealroulette/
  backend/
    alembic/
    mealroulette/
      api/
        routes/
        dependencies.py
      auth/
      core/
        config.py
        security.py
      db/
        base.py
        session.py
      models/
      schemas/
      services/
        ingredients/
        planning/
        shopping/
        telegram/
        backups/
        llm/
      worker.py
      main.py
    tests/
    Dockerfile
    pyproject.toml
  frontend/
    src/
      api/
      app/
      components/
      features/
        auth/
        dishes/
        planning/
        shopping/
        cooking/
        settings/
      routes/
      styles/
    Dockerfile
    package.json
  docs/
    CURSOR_ROADMAP.md
    LOCALIZATION.md
    MVP.md
  SPECS.md
  backups/
    .gitkeep
  docker-compose.yml
  .env.example
  README.md
```

## Architecture Decisions

### Backend

- Use Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL, and psycopg.
- Use layered modules:
  - `models`: SQLAlchemy tables and relationships.
  - `schemas`: Pydantic request and response contracts.
  - `api/routes`: thin HTTP handlers.
  - `services`: business logic, validation, aggregation, scheduling, and integrations.
  - `db`: engine, sessions, and migration glue.
- Keep route handlers thin. Validation and write orchestration belong in services.
- Use UUID or integer primary keys consistently. Integer IDs are acceptable for a self-hosted app.
- Use timezone-aware timestamps.
- Use enum types for role, meal slot, item status, plan status, backup status, backup type, unit dimension, seasonality mode, and seasonality strength.

### Frontend

- Use React + Vite unless intentionally switching to SvelteKit.
- Use a mobile-first shell with authenticated routes.
- Keep feature modules separated by domain: auth, dishes, planning, shopping, cooking, settings.
- Use generated or hand-maintained API client functions under `src/api`.
- Avoid landing-page style UI. The first authenticated screen should be the Today view.

### Worker

- Use APScheduler in `backend/mealroulette/worker.py`.
- The worker should share backend configuration and services.
- Jobs:
  - daily Telegram reminder
  - scheduled backups
  - optional automatic plan generation

### Deployment

- Use Docker Compose with `api`, `worker`, `frontend`, and `db`.
- Mount `./backups:/backups`.
- Keep `.env.example` complete and safe to commit.
- Do not commit real secrets.

### Testing

- Backend: `pytest`, `pytest-asyncio`, `httpx`.
- Frontend: `Vitest`, React Testing Library.
- Keep service logic testable without HTTP where possible.
- Use a dedicated test database or rollback fixtures for integration tests.
- Add a root `Makefile` or documented npm/poetry scripts for `test`, `test-unit`, and `test-integration`.

### Quality Gates

Run tests automatically at these points:

- pre-commit: fast backend and frontend test suites
- CI on push and pull request: full test suite
- manual: during development before opening a PR

Recommended tooling:

- `pre-commit` for local commit hooks
- GitHub Actions for CI

The default commit hook should fail if tests fail. Lint/format hooks may run in the same pre-commit configuration.

## Implementation Phases

Phases 0–11 shipped through **`v0.8.0`**. Phases 12–13 cover LLM/localization and v1 hardening.

| Phase | Name | Target version |
| --- | --- | --- |
| 9 | Computed recipe traits & catalog keys | v0.6 |
| 10 | Cooking mode | v0.7 |
| 11 | Taxonomy hardening + backup, export, import | v0.8 |
| 12 | LLM-assisted entry & localization | v0.9 |
| 13 | v1 hardening | v1.0 |

### Phase 0 - Project Bootstrap

Deliverables:

- Root `README.md`
- `docker-compose.yml`
- `.env.example`
- `backend` FastAPI project with `/health`
- `frontend` Vite app with a minimal shell
- PostgreSQL service
- Basic developer commands documented
- `pre-commit` configuration
- GitHub Actions workflow for tests
- Initial backend health-check integration test
- Initial frontend smoke test

Acceptance criteria:

- `docker compose up --build` starts all services.
- API health endpoint returns `{"status":"ok"}`.
- Frontend can call the API health endpoint.
- `pytest` passes for the backend bootstrap tests.
- Frontend test command passes for the initial shell test.
- Pre-commit runs the test suite before allowing a commit.
- CI runs the same test suite on push and pull request.

### Phase 1 - Backend Foundation

Deliverables:

- SQLAlchemy setup
- Alembic setup
- Config management
- Database session dependency
- Error handling conventions
- Backend unit and integration test harness
- Test database fixture strategy
- First migration

Acceptance criteria:

- Alembic can create and upgrade the schema.
- Tests can run against an isolated test database or transaction fixture.
- API responses use predictable error payloads.
- At least one integration test exercises database connectivity through the API layer.

### Phase 2 - Authentication and Users

Deliverables:

- User model
- Password hashing
- Login/logout/refresh/me endpoints
- Role-based dependencies
- Initial admin creation command or bootstrap flow

Acceptance criteria:

- Unauthenticated users cannot access protected endpoints.
- Admin-only endpoints reject normal users.
- Password hashes are never returned.

### Phase 3 - Core Catalog Data

Deliverables:

- Dishes
- Recipes
- Recipe steps
- Ingredients
- Ingredient aliases
- Units
- Ingredient-specific unit conversions
- Tags
- Dish tags
- Seasonality

Acceptance criteria:

- A user can create a dish with at least one recipe, structured steps, ingredients, tags, and seasonality.
- Unknown ingredient insertion follows the confirm/create/map flow at the API level.
- Seed data includes base units and starter tag families.

Implementation notes:

- Reference units and tags live in `backend/mealroulette/data/reference/*.yaml` and are loaded idempotently after migrations (`seed_reference_data` CLI / API entrypoint).
- Unit compatibility and aggregation rules are implemented in `mealroulette.services.quantities` (consumed by Phase 6 shopping lists).
- Alembic revisions `005`–`010` extend catalog classification, recipe ownership, main recipe, image URL, and simplified course enum (`004` is a no-op placeholder) — see root [README.md](../README.md#database-migrations-alembic).

### Phase 4 - Frontend Shell and Dish Library

**Status:** Done — merged in PR #3 (`v0.1.0`, commit `b41cdae`).

Deliverables:

- Login screen
- Authenticated app layout
- Dish list (card grid with image URL or emoji placeholder)
- Dish detail
- Add/edit dish form (structured food profile, planning profile, seasonality)
- Recipe variant editing (separate routes; ingredients and steps)
- Tag and ingredient selection

Acceptance criteria:

- A household can manually enter realistic recipes from the UI.
- Mobile layout remains usable for dish creation and viewing.

Implementation notes (v0.1):

- **Dish vs recipe:** dishes hold name, course, tags, planning flags, seasonality, optional `image_url`; recipes hold variant name, servings, type, difficulty, prep/cook times, ingredients, and steps.
- **Main recipe:** exactly one recipe per dish is `is_main` (first recipe by default). Dish-level difficulty and prep/cook shown in the UI come from the main recipe.
- **`thermomix_possible`:** computed when any recipe has `recipe_type = thermomix` (read-only on dish).
- **Course:** `starter`, `main`, or `dessert` only.
- **Seasonality:** `all_year` or `seasonal` with `preferred_months` only (no strength / allowed / excluded modes in UI).
- **Tags:** seeded families are `protein`, `carb`, `style`, `temperature` — see `backend/mealroulette/data/reference/tags.yaml`.
- **Not in v0.1 UI:** dish library search/filters, dietary flags (planned: infer from recipe ingredients later), cuisine tags.

### Phase 5 - Manual Meal Planning

**Status:** Done — merged in PR #4 (`v0.2.0`, commit `fb20858`).

Deliverables:

- Meal plans
- Meal plan items
- Weekly plan API
- Current plan API
- Manual assignment
- Lock/unlock
- Mark meal as eaten (`eaten`)
- Skip meal (`skipped`, with optional `skip_reason` / `skip_comment`)
- Ate leftovers (`ate_leftovers`, optional `leftover_source_item_id`)
- Ratings
- Meal history derived from item status changes

**Lightweight leftovers only (Phase 5 scope):**

- Track what was eaten at each meal slot — not prepared-food inventory.
- `ate_leftovers` may reference a prior `meal_plan_item` as `leftover_source_item_id`, or use **Unknown / same dish** (`null`).
- Valid sources: status `eaten` only (not `ate_leftovers` — no fake leftover chains), within the **last 7 days** relative to the current meal date, same day or earlier.
- `ate_leftovers` meals do not become new leftover sources.
- UI actions: **Ate as planned**, **Ate leftovers**, **Skipped**.

**Deferred to a later phase (after shopping lists):**

- `leftover_batch` inventory (portions, fridge/freezer, expiration)
- Portion decrement and manual corrections
- Scheduling from available leftover stock
- Shopping-list exclusion for meals made from prepared leftovers

Acceptance criteria:

- User can plan lunch and dinner for a week manually.
- Locked items remain locked.
- Eaten/skipped/ate_leftovers state is stored and visible.
- Ratings affect stored dish/user rating records.

**Implementation notes (do not treat "cooked" as meal completion):**

- Meal item statuses: `planned`, `eaten`, `skipped`, `ate_leftovers`.
- UI workflows: **Plan** (assign dish/recipe, lock) and **Review** (execution status, rating).
- Review display: past/today `planned` shows as **Not reviewed**.
- Execution actions only for today/past; future meals read-only in Review.
- **Undo status** resets to `planned`, clears execution metadata and meal rating.
- `leftover_source_item_id` optional when marking `ate_leftovers`; source must be status `eaten`, within 7 days, same day or earlier. `ate_leftovers` meals are not valid sources.
- Do **not** implement portion inventory, fridge/freezer tracking, expiration, or automatic leftover stock decrement in Phase 5.
- Optional `servings_planned` / `servings_eaten` only if cheap — must not drive inventory logic.

Implementation notes (v0.2):

- Alembic revisions `011`–`014`: meal plans, plan items, statuses, `meal_ratings`, `review_saved_at`.
- Planning API: `/api/planning/current`, week plan CRUD, assign dish/recipe, lock, mark eaten/skip/ate leftovers, reset, ratings.
- `review_saved_at`: Review tab filters "needs review" until rating saved (eaten), skip saved, or leftover source confirmed.
- Frontend: `/plan` and `/review` with shared `WeekPlanShell`, `MealSlotCard`, `StarRating`.
- Mobile polish: bottom tab bar, review-first default route, compact week navigation, safe-area padding, larger touch targets.
- Swagger OAuth2 password flow via `POST /api/auth/token` for `/docs` Authorize.
- Reroll / auto-scheduler deferred to Phase 8.

### Phase 6 - Shopping Lists

**Status:** Done — merged in PR #5 (`v0.3.0`, commit `88d2675`).

**Prerequisite tooling (done on this branch):**

- YAML dish fixture import (`import_sample_dishes`) loads `data/fixtures/sample_dishes.yaml` for realistic catalog data during development. Idempotent by dish name. Not the Phase 11 JSON backup format.
- YAML ingredient seed import (`import_ingredient_seed`) loads `data/fixtures/mealroulette_ingredients_seed.yaml` — canonical ingredients, aliases, units, and unit conversions. Idempotent; bootstrap-approves medium-or-better conversions for `allow_approximate_conversion` ingredients unless `approved: false` is set explicitly. Replaces the legacy `reference/ingredient_conversions.yaml` file (now deprecated).

**Recommended bootstrap order** (after `alembic upgrade head`):

1. `python -m mealroulette.commands.import_ingredient_seed`
2. `python -m mealroulette.commands.import_sample_dishes`

Deliverables:

- Dynamic shopping list generation
- Optional persisted shopping lists
- Shopping list items with per-meal source contributions
- Shopping list generator calling `mealroulette.services.quantities` for aggregation
- Pantry filtering
- Category grouping
- Source meal references and planned-meals summary in UI
- Shopping list UI (`/shopping`)
- Ingredient unit behavior fields (family, preferred shopping unit, aggregation unit/strategy)
- Ingredient unit conversions with `approved` / `source` / `confidence` metadata
- Ingredient conversions CRUD API
- Ingredient admin dashboard (`/ingredients` list + edit: aliases, conversions, unit behavior)
- Ingredient seed catalog for household-relevant units and approximate conversions

Acceptance criteria:

- Compatible units aggregate through base units.
- Incompatible units remain separate unless an approved ingredient-specific conversion exists.
- Cross-dimension aggregation respects per-ingredient `aggregation_strategy` (e.g. carrot mass + count → `~860 g`).
- Shopping items show which planned meals require them.
- Admins can review and approve conversion suggestions from the ingredient dashboard.

**Deferred to Phase 12:** multilingual content translations — design in [LOCALIZATION.md](LOCALIZATION.md).

Implementation notes (v0.3):

- Alembic revisions `015`–`018`: shopping lists, per-meal contributions, ingredient unit behavior, conversion uniqueness.
- Shopping API: preview (`GET /api/shopping-list`), create/fetch lists, check-off items.
- `services/quantities`: strategy-aware aggregation; approved conversions only for cross-dimension merge.
- Ingredient seed: `import_ingredient_seed` + `mealroulette_ingredients_seed.yaml`.
- Frontend: `/shopping` (List tab), `/ingredients` admin catalog and edit.
- Localization design documented; implementation deferred to Phase 12.

### Later — Leftover inventory (after shopping lists)

Not part of Phase 5. Introduce when shopping-list generation can exclude ingredients for meals made from prepared leftovers.

Deliverables:

- `leftover_batch` records (dish, recipe, portions, storage, cooked_at, expires_at)
- Portion accounting and manual corrections
- Schedule meals from available leftover stock
- Shopping-list exclusion for meals sourced from leftovers

### Phase 7 - Telegram Reminders

**Status:** Released as [`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0) (merge `a560e7a`, PR #7).

Deliverables:

- Telegram settings API
- Subscriber model (`/subscribe`, `/unsubscribe`)
- Test message endpoint
- Daily reminder service
- APScheduler worker + `getUpdates` polling for bot commands
- Manual send endpoint
- On-demand commands (`/planning`, `/reminder`, `/shopping`)
- HTML message formatting
- Recipe deep links in planning (tap dish → full recipe)
- Send saved shopping list via Telegram
- Ingredient category reference + editor dropdown

Acceptance criteria:

- Admin can configure reminder schedule without exposing the bot token in API responses.
- Manual send uses the same code path as the scheduled job.
- Disabled settings prevent sends.
- Subscribers receive broadcasts; `/subscribe` registers chat IDs.

#### Implementation notes (v0.4)

- Alembic revision `019`: `telegram_settings`, `telegram_subscribers`.
- Bot token in `TELEGRAM_BOT_TOKEN` (`.env` / Docker); optional `TELEGRAM_BOT_USERNAME` for `t.me` recipe deep links. *(Original plan: Fernet-encrypted token in DB — simplified for self-hosting.)*
- Worker: APScheduler minute poll for `daily_reminder_time`; parallel `getUpdates` loop for commands.
- HTML formatters: `telegram_format_html.py`, `telegram_recipe.py` (ingredients + steps); safe truncation via `telegram_html_utils.py`.
- Admin UI: `/settings/telegram` — schedule, test, send now, subscriber list.
- Ingredient polish: `reference/ingredient_categories.yaml`, `GET /api/ingredient-categories`, seed import backfill.
- Release notes: [docs/releases/v0.4.0.md](releases/v0.4.0.md).

#### Original implementation plan (v0.4)

**1. Database & secrets**

- Migration `019_telegram_settings`: singleton household row (`telegram_settings` table per SPECS §7.19).
- Fields: `enabled`, `daily_reminder_time`, `shopping_window_days`, `include_today`, `include_pantry_items`, `group_by_category`, `timezone`, `last_sent_at`, `last_error`, `last_update_id`.
- `telegram_subscribers` table replaces fixed `chat_id` in settings.
- Bot token via environment variable (not stored in DB).

**2. Backend services (reuse shopping logic)**

- `TelegramSettingsService` — get/update singleton settings; token from env.
- `TelegramMessageFormatter` / `telegram_format_html` — HTML messages from shopping list and meal plan data; 4096-char limit with safe truncation.
- Daily scheduled reminder and **Send reminder now** use the same HTML path as `/reminder` (`TelegramOnDemandService.build_reminder_message`).
- `TelegramOnDemandService` — `/planning`, `/reminder`, `/shopping` on-demand messages.
- `TelegramUpdateService` — poll `getUpdates`, handle commands and recipe deep links.
- `TelegramClient` — `sendMessage`, `getUpdates`, `getMe` (httpx).

**3. API routes** (admin-only)

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/telegram/settings` | Settings without secrets |
| `PUT` | `/api/telegram/settings` | Update schedule flags |
| `GET` | `/api/telegram/subscribers` | List subscribers |
| `POST` | `/api/telegram/test` | Send fixed test message |
| `POST` | `/api/telegram/send-daily-reminder` | Manual run (same code path as worker) |
| `POST` | `/api/shopping-lists/{id}/send-telegram` | Send a saved list |

**4. Worker**

- APScheduler `BackgroundScheduler` in `worker.py`.
- Minute poll compares `daily_reminder_time` + `enabled` + subscribers.
- `getUpdates` loop handles `/subscribe`, `/planning`, recipe links, etc.

**5. Frontend** (admin Settings screen)

- Route `/settings/telegram` — link from header for admins.
- Form: enabled, reminder time, window days, include today, include pantry, group by category, timezone.
- Actions: **Save**, **Send test**, **Send reminder now**.
- Subscriber list; `TELEGRAM_BOT_TOKEN` setup instructions.

**6. Tests**

- Formatters (HTML planning, reminder, shopping, recipe).
- Settings and subscriber requirements.
- API integration with mocked Telegram.
- Update handler (`/subscribe`, `/planning`, `/start recipe_<id>`).

**7. Docs & release**

- `README.md` — BotFather setup, `/subscribe`, recipe links.
- `.env.example` — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`.
- Tagged [`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0), [docs/releases/v0.4.0.md](releases/v0.4.0.md).

**Suggested commit slices**

1. Migration + models + settings API
2. Formatter + reminder service + Telegram client + API send endpoints
3. Worker + APScheduler + update polling
4. On-demand commands + HTML formatters + recipe links
5. Frontend settings UI + ingredient categories
6. Tests + docs

### Phase 8 - Explainable Scheduler

**Status:** Done — shipped as [`v0.5.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.5.0) (PR #8).

#### Product behaviour

Three roulette triggers share one engine (`SchedulerService`):

| Trigger | Scope | Locked meals | Dates |
| --- | --- | --- | --- |
| **Reroll** | One slot, user-initiated | Preserved | Today and future only |
| **Generate week** | All unlocked/auto-eligible slots in a week | Preserved | Configurable week (default: next Mon–Sun) |
| **Scheduled roulette** | Same as generate week | Preserved | Worker job (e.g. Friday 18:00 → following week) |

- **Undo:** snapshot dish/recipe/reasons before reroll or generate; restore last action from Plan UI.
- **No reroll** for yesterday or earlier — past meals stay as review/history.
- **Manual assign** sets `manually_selected=true` and clears auto reasons; scheduler skips those slots unless user unlocks/regenerates.

#### Tags vs vectors (separation of concerns)

| Mechanism | Used for |
| --- | --- |
| **Dish tags** (`protein`, `carb`, `style`, …) | Weekly targets, hard/soft constraints, selection reasons |
| **Family vector** | Similarity only — avoid repeating the same *kind* of meal recently |

Do **not** use ML embeddings (per SPECS §10). Vectors are sparse proportion dicts built **on the fly** from the main recipe. **Full calculation rules:** [docs/SCHEDULER.md](SCHEDULER.md).

#### Family vector (summary)

See **[SCHEDULER.md](SCHEDULER.md)** for the authoritative spec. Summary:

1. Main-recipe lines → **grams** (mass / volume / count rules).
2. **Count:** approved unit→g conversion if present; else **default 100 g × count** (never skip the line).
3. **Volume:** ml path when possible; else **1 ml ≈ 1 g** reference.
4. Roll up to `ingredient.family` (fallback: category, canonical name).
5. Exclude `pantry_item` and lines &lt; 5 g before rollup.
6. L1-normalize to **percentages** (sparse dict).
7. **Cosine similarity** for distance `1 - cosine` vs recent **eaten** meals; same dish in window = hard exclude.

Configurable defaults in `planning_rules.rules_json`: `default_grams_per_count` (100), `vector_min_grams` (5).

**History profile:** built at roulette time from `meal_history` — no stored embedding table.

#### Scoring (soft)

Combine: seasonality for slot date, rating boost/penalty, weekly target progress (with **tolerance** in `planning_rules.rules_json`), history similarity penalty, weighted random among top candidates (50 plan attempts per SPECS §12.5).

#### Scheduled roulette + Telegram

Singleton **`scheduler_settings`** (mirror Telegram settings pattern):

- `enabled`, `run_weekday` (e.g. 4 = Friday), `run_time`, `timezone`
- `target_week_offset` (default `1` = next Mon–Sun, time to shop before the week)
- `notify_telegram`, `notify_planning_days` (default 7)

Worker minute poll (same as daily reminder). On success, broadcast **“New roulette”** + HTML planning message to subscribers (reuse `format_planning_message_html`).

#### Deliverables

- Migration `020`: `planning_rules`, `scheduler_settings`, optional undo snapshot storage
- `services/scheduler/` — vector builder, cosine similarity, constraints, scoring, generator
- `SchedulerService` — generate week, reroll, undo
- `SchedulerSettingsService` + admin UI `/settings/scheduler`
- API: `POST /meal-plans/{id}/generate`, `POST /meal-plan-items/{id}/reroll`, `POST /meal-plans/{id}/undo-roulette`
- Plan UI: Generate week, Reroll, Undo, show selection reasons
- Tests: vector math, constraints, locked meals, date guards, scheduled job, Telegram notify

#### Acceptance criteria

- Scheduler never modifies locked or manually selected meals (unless user regenerates explicitly).
- Reroll blocked for past dates.
- Hard constraints: inactive dishes, same-dish window, weekly target caps (+ tolerance).
- Each auto item stores human-readable `selection_reasons_json` (targets, seasonality, similarity to recent meals).
- Scheduled Friday job fills next week and optionally notifies Telegram.
- Undo restores previous assignments from last roulette action.

#### Suggested commit slices

1. Planning rules + scheduler settings (migration, seed, admin API)
2. Family vector + cosine similarity + unit tests
3. Scoring engine + 50-attempt generator
4. Reroll + generate + undo API + temporal neighbours + swap ✅
5. Plan UI + reasons display + plan-from-gallery ✅
6. Worker scheduled job + Telegram “New roulette” ✅
7. Tests, docs, release notes `v0.5.0.md` ✅

Acceptance criteria (summary):

- Scheduler never modifies locked meals.
- Scheduler respects hard constraints.
- Each automatic item stores human-readable selection reasons.
- Reroll replaces only the selected item (today/future).

### Phase 9 - Computed Recipe Traits & Catalog Keys

**Status:** Shipped in **`v0.6.0`** via PR #9.

**Goal:** Add stable public keys, ingredient food groups, and computed recipe traits while keeping v0.5 behaviour intact — especially weekly target settings, scheduler generation/reroll, dish catalog, recipe variants, shopping list, planning UI, and Telegram planning output.

**Compatibility strategy (additive first):**

- Keep dish tags (`tags`, `dish_tags`, tag editor, `DishCandidate.tag_names`, protein/carb/style tag sets).
- Keep weekly target matching on **dish tags** in the first implementation pass (`dish_matches_weekly_target` unchanged except optional tested fallback later).
- Computed traits are metadata for display, filtering, and future scheduler migration — not a replacement for tags yet.
- Shopping list aggregation semantics unchanged.
- Telegram planning output unchanged (traits in messages = separate future feature).

**Reference:** detailed compatibility rules and JSON shapes will live in `docs/COMPUTED_TRAITS.md` (commit slice 1).

#### Public keys

Keep integer primary keys internally. Add unique public key columns.

Constants:

```text
DISH_PUBLIC_KEY_LENGTH = 32
DISH_PUBLIC_KEY_MAX_SLUG_LENGTH = 20
DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH = 8
RECIPE_SEQUENCE_WIDTH = 3
```

- **Dish:** `<slug>-<random_suffix>` — total length 32; slug max 20; random suffix fills remainder (min 8); generated once; **does not change when dish name changes**; globally unique.
- **Recipe:** `<dish_public_key>-001` — sequence width 3 minimum, grows for 1000+; unique per dish; normally length 36, with database capacity up to 40.
- Random alphabet: `0123456789abcdefghjkmnpqrstvwxyz`

#### Ingredient food groups

Add `ingredients.food_group` with controlled vocabulary:

```text
vegetable, carbohydrate, meat, fish, seafood, egg, dairy, cheese, legume,
plant_protein, fat, condiment, herb, spice, stock, fruit, fungus, alcohol,
pantry, other
```

Centralize category→food-group mapping in one backend module. Unknown category → `other` unless explicit `food_group` is set.

Initial category mapping:

```text
vegetable -> vegetable
grain -> carbohydrate
pasta -> carbohydrate
bread -> carbohydrate
pastry -> carbohydrate
potato -> carbohydrate
meat -> meat
fish -> fish
seafood -> seafood
egg -> egg
dairy -> dairy
cheese -> cheese
legume -> legume
plant_protein -> plant_protein
fruit -> fruit
fungus -> fungus
condiment -> condiment
herb -> herb
spice -> spice
stock -> stock
alcohol -> alcohol
pantry -> pantry
canned -> pantry
frozen -> other
preserved -> pantry
```

Explicit `food_group` on an ingredient overrides category inference.

#### Computed recipe traits

Store on `recipes.computed_traits_json`. Example shape:

```json
{
  "family_vector": { "rice_family": 62.5, "chicken_family": 37.5 },
  "food_group_weights": { "carbohydrate": 62.5, "meat": 37.5 },
  "contains_food_groups": ["carbohydrate", "meat"],
  "contains_meat": true,
  "vegan": false,
  "carb_heavy": true,
  "dominant_carb": "rice_family",
  "dominant_protein": "chicken_family"
}
```

Rules (Phase 9):

- Exclude `pantry_item=true` ingredients from percentage-based vectors and traits.
- `vegan=false` if any non-pantry ingredient has food group in `{meat, fish, seafood, egg, dairy, cheese}`.
- `contains_meat=true` only for food group `meat` (fish/seafood are not meat).
- `carb_heavy=true` when carbohydrate percentage ≥ **33.0** (`CARB_HEAVY_THRESHOLD_PCT`, hard-coded).
- `dominant_carb` = highest-weight family among carbohydrate ingredients.
- `dominant_protein` = highest-weight family among `{meat, fish, seafood, egg, dairy, cheese, legume, plant_protein}`.

Do **not** infer style tags such as `soup` from ingredients in Phase 9.

#### Effective traits (read model)

- **Dish** `computed_traits_json` = main recipe traits.
- **Meal plan item** `computed_traits_json` = selected recipe traits if `recipe_id` set, else dish main recipe traits (display/filter metadata only; assignment semantics unchanged).

#### Trait refresh

Refresh recipe traits when:

- recipe ingredient is added, updated, or deleted;
- ingredient `category`, `food_group`, `family`, or `pantry_item` changes;
- approved unit conversion relevant to recipe quantities changes.

Prefer explicit service-level refresh over hidden ORM events unless the repo already establishes that pattern.

#### Scheduler integration (parallel only)

Add `DishCandidate.computed_traits_json` from main recipe traits. Do **not** change weekly target matching in the first pass. Optional later step: tag-first matching with explicit computed-trait fallback and mapping tests (`fish`→seafood food group, `pasta`/`rice`→dominant/family vector, `soup` stays tag/style-based).

#### Migration plan

New Alembic revision after current latest:

1. Add nullable columns: `ingredients.food_group`, `dishes.public_key`, `recipes.public_key`, `recipes.sequence_number`, `recipes.computed_traits_json`.
2. Backfill food groups from category mapping.
3. Backfill dish public keys and recipe sequence numbers (main recipe first if present, then remaining recipes by recipe id).
4. Backfill recipe public keys.
5. Compute recipe traits.
6. Enforce NOT NULL + unique indexes on public keys and per-dish sequence.

#### API exposure

Add fields:

- `IngredientPublic.food_group` (+ create/update requests)
- `DishPublic.public_key`, `DishPublic.computed_traits_json`
- `RecipePublic.public_key`, `RecipePublic.sequence_number`, `RecipePublic.computed_traits_json`
- `MealPlanItemPublic.computed_traits_json`

#### Frontend scope (minimal)

- Update TypeScript API types.
- Ingredient editor: food group field.
- Show computed traits only where useful and non-disruptive.
- Preserve weekly targets settings UI (`/settings/targets`) and tag editor.

#### Test requirements

Backend:

- public key generation (length, uniqueness, stability after dish rename);
- recipe sequence and public key generation per dish;
- ingredient food-group mapping from category and explicit override;
- recipe computed traits (meat, vegan, carb-heavy, dominant carb, dominant protein);
- dish inherits main recipe traits; meal-plan item uses selected recipe traits;
- migration/backfill behaviour;
- **existing scheduler and weekly-target tests still pass**.

Frontend:

- typecheck and build;
- weekly target add/remove/save still works (`/settings/targets`).

#### Out of scope for initial pass

Do **not** in Phase 9 unless explicitly approved later:

- delete dish tags or remove the tag editor;
- replace weekly target matching wholesale (optional tag-first fallback only with explicit tests);
- replace integer primary keys;
- redesign scheduler UX;
- make trait thresholds configurable (`CARB_HEAVY_THRESHOLD_PCT` stays hard-coded at 33.0);
- infer style tags such as `soup` from ingredients;
- alter shopping-list aggregation semantics;
- require computed traits for Telegram message formatting.

#### Deliverables

- `docs/COMPUTED_TRAITS.md` — full spec and compatibility statement ✅
- `docs/TAXONOMY_AND_RESOLVER.md` — taxonomy and resolver spec ✅
- Migration `022_computed_traits` + backfill + trait computation services ✅
- Public key generation + tests ✅
- Ingredient food groups + category mapping ✅
- Ingredient resolver + taxonomy browsing APIs ✅
- API and frontend exposure (catalog, planning, taxonomy navigator) ✅
- Scheduler candidate field (tags unchanged) ✅
- Release notes `docs/releases/v0.6.0.md` ✅

#### Acceptance criteria

- Public keys stable after dish rename; unique; correct lengths.
- Recipe sequences and public keys correct per dish.
- Trait computation correct for representative meat, vegan, carb-heavy, dominant carb/protein cases.
- Dish and meal-plan item expose effective traits as specified.
- **All existing scheduler and weekly-target tests still pass.**
- Weekly targets presets (`fish`, `meat`, `vegetarian`, `pasta`, `rice`, `soup`) still match via tags.
- Shopping list behaviour unchanged.
- `cd backend && python3.12 -m pytest`, `cd frontend && npm test -- --run`, `npm run build` green.

#### Suggested commit slices

1. Document Phase 9 spec (`docs/COMPUTED_TRAITS.md`)
2. Add stable public keys for dishes and recipes
3. Add ingredient food groups
4. Compute and store recipe traits + refresh hooks
5. Expose effective dish and meal-plan traits
6. Add computed traits to scheduler candidates (no tag-target replacement)
7. Update frontend types and minimal trait display
8. Update imports, seeds, docs, tests, release notes

### Phase 10 - Cooking Mode

**Status:** Done — [`v0.7.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.7.0), PR [#10](https://github.com/didac-crst/mealroulette/pull/10). Spec: [COOKING_MODE.md](COOKING_MODE.md).

Delivered:

- **`/today` home** — today's lunch/dinner cards; default route after login
- **Cook** and **Review** on each today card (Review expands inline; week Review tab unchanged)
- Route `/recipes/:recipeId/cook` and **Cook** entry from recipe detail
- Step-by-step cooking viewer with Previous / Next, step timers, and running-timers bar
- Browser chime + optional notification when a timer finishes; Telegram timer alerts (migration `026`)
- Full recipe ingredient list in a collapsible panel; dish library real-time search
- Mobile-first layout; local step index only (no persistent session)

Deferred to later slices (see spec):

- Thermomix step badges and appliance layout
- Persistent cooking sessions, voice, Telegram deep links

Acceptance criteria:

- User lands on Today and can cook or review today's meals from a phone.
- User can open cooking mode from Today or recipe detail and return to it.
- User can walk through steps and see ingredients on a phone-sized viewport.
- Recipe detail/edit flows and backend behaviour unchanged.
- Frontend tests and build pass.

### Phase 11 - Taxonomy Hardening + Backup, Export, and Import

**Status:** Done — shipped as [`v0.8.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.8.0), PR [#11](https://github.com/didac-crst/mealroulette/pull/11), merge `f5ec043`. Handoff: [PHASE11_HANDOFF.md](PHASE11_HANDOFF.md). ADR: [002-canonical-taxonomy-before-backup.md](adr/002-canonical-taxonomy-before-backup.md). Backup spec: [BACKUP_EXPORT_IMPORT.md](BACKUP_EXPORT_IMPORT.md).

**Order of work:**

1. **Taxonomy hardening** — `food_groups` and `ingredient_families` tables; `ingredients.family_id` FK; canonical ingredient enforcement; migrate weekly targets from tags to computed traits (with temporary fallback); curated classifications for non-derivable concepts (`soup`, …).
2. **Backup contract** — JSON export/import, run tracking, retention, optional `pg_dump`, restore docs — format reflects hardened taxonomy.

Deliverables (backup slice):

- Full JSON export
- Full JSON import
- Backup run tracking
- Optional `pg_dump` backup
- Scheduled backup job
- Retention cleanup
- Restore documentation

Acceptance criteria:

- Taxonomy tables and FK integrity enforced before backup ships.
- Weekly target matching uses computed traits for derivable targets (legacy tag fallback documented and removable).
- JSON export includes food groups, families, canonical ingredients, and related reference data.
- Import validates shape and referential integrity before writing.
- Backup files are written under `/backups`.
- Old backups are removed according to retention settings.

### Phase 12 - LLM-Assisted Entry & Localization

**Status:** Not started. Design spec: [LOCALIZATION.md](LOCALIZATION.md).

Deliverables:

- Provider abstraction
- LLM settings
- Enrich dish endpoint
- Suggest ingredients endpoint
- Suggest tags endpoint
- Normalize ingredients endpoint
- Draft review UI
- **Localization foundation:** `translations` table with `status`, `source_text_hash`, review metadata; `default_locale` on dish/recipe/ingredient
- **Localization jobs:** `localization_jobs` + `localization_job_items` for one-click bulk translate
- **Glossary:** protected terms and consistent culinary vocabulary for LLM prompts
- **Bulk translate:** field-aware batched `POST /api/admin/localization/jobs` → draft translations → admin approve
- **Locale-aware reads:** `?locale=fr` with fallback chain; UI chrome via frontend i18n (separate from content)
- Optional: LLM-suggested ingredient **aliases** per target locale (not a substitute for display translations)

Acceptance criteria:

- LLM endpoints require authentication.
- LLM output is saved only after explicit user confirmation.
- Ingredient suggestions still pass through normalization flow.
- Approved translations are served deterministically; stale translations are not shown to normal users.
- Bulk translation is idempotent (unique `entity_type + entity_id + field_name + locale`).
- Source text changes mark approved translations as `stale`.
- Recipe step translation preserves quantities, times, temperatures, units, and appliance terms.
- Ingredient display translations remain separate from search aliases.

### Phase 13 - v1 Hardening

Deliverables:

- End-to-end happy path tests
- API tests for all write endpoints
- Frontend smoke tests
- Raspberry Pi deployment notes
- Security review of settings and auth flows
- Error and empty-state polish

Acceptance criteria:

- A household can use the app for real weekly planning.
- Backup and restore are documented and tested.
- Scheduler is explainable enough to debug bad plans.

## Cursor Task Rules

When asking Cursor to implement work:

1. Point it to `SPECS.md` and this roadmap.
2. Ask for one phase or one vertical slice at a time.
3. Require unit tests for service logic and integration tests for API endpoints before moving to the next phase.
4. Require migrations for every schema change.
5. Require the pre-commit and CI test workflows to stay green.
6. Reject schema shortcuts that duplicate ingredient names, hardcode food categories as columns, or bypass aliases.
7. Keep generated code aligned with existing repository patterns.

## Suggested First Cursor Prompt

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
- basic backend tests

Do not implement domain models yet except what is necessary for Alembic/bootstrap.
Keep the repository structure aligned with docs/CURSOR_ROADMAP.md.
```

## Definition of Done for v1

- Unit and integration tests cover core services and write endpoints.
- Pre-commit and CI both run the project test suites successfully.
- Authenticated household users can manage dishes, recipes, ingredients, aliases, tags, ratings, and meal plans.
- Weekly lunch and dinner plans can be created manually and generated automatically.
- Shopping lists aggregate ingredients correctly without fake precision.
- Telegram reminders work from the same shopping-list logic.
- Cooking mode works on mobile.
- Backups can be exported, imported, scheduled, retained, and restored.
- Scheduler selections are explainable.
- LLM-assisted entry is optional and draft-only.
