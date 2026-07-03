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

**Status:** Done — merged in PR #5 (`v0.3.0`).

**Prerequisite tooling (done on this branch):**

- YAML dish fixture import (`import_sample_dishes`) loads `data/fixtures/sample_dishes.yaml` for realistic catalog data during development. Idempotent by dish name. Not the Phase 10 JSON backup format.
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

**Deferred to Phase 11:** multilingual content translations — design in [LOCALIZATION.md](LOCALIZATION.md).

Implementation notes (v0.3):

- Alembic revisions `015`–`018`: shopping lists, per-meal contributions, ingredient unit behavior, conversion uniqueness.
- Shopping API: preview (`GET /api/shopping-list`), create/fetch lists, check-off items.
- `services/quantities`: strategy-aware aggregation; approved conversions only for cross-dimension merge.
- Ingredient seed: `import_ingredient_seed` + `mealroulette_ingredients_seed.yaml`.
- Frontend: `/shopping` (List tab), `/ingredients` admin catalog and edit.
- Localization design documented; implementation deferred to Phase 11.

### Later — Leftover inventory (after shopping lists)

Not part of Phase 5. Introduce when shopping-list generation can exclude ingredients for meals made from prepared leftovers.

Deliverables:

- `leftover_batch` records (dish, recipe, portions, storage, cooked_at, expires_at)
- Portion accounting and manual corrections
- Schedule meals from available leftover stock
- Shopping-list exclusion for meals sourced from leftovers

### Phase 7 - Telegram Reminders

Deliverables:

- Telegram settings API
- Secret-safe response schema
- Test message endpoint
- Daily reminder service
- APScheduler job
- Manual send endpoint

Acceptance criteria:

- Admin can configure Telegram without exposing the token afterward.
- Manual send uses the same formatting and aggregation as the scheduled job.
- Disabled settings prevent sends.

### Phase 8 - Explainable Scheduler

Deliverables:

- Planning rules
- Rule-based meal similarity
- Seasonality scoring
- Rating scoring
- Recent dish avoidance
- Weekly target scoring
- 50-attempt candidate plan generation
- Reroll one meal
- Selection reasons persisted on meal plan items

Acceptance criteria:

- Scheduler never modifies locked meals.
- Scheduler respects hard constraints.
- Each automatic item stores human-readable selection reasons.
- Reroll replaces only the selected item.

### Phase 9 - Cooking Mode

Deliverables:

- Step-by-step recipe viewer
- Previous/next controls
- Optional timer
- Thermomix metadata display
- Ingredient reference panel
- Mobile-readable layout

Acceptance criteria:

- User can cook a recipe from a phone without editing data.
- Timers can be started from steps that define timer metadata.

### Phase 10 - Backup, Export, and Import

Deliverables:

- Full JSON export
- Full JSON import
- Backup run tracking
- Optional `pg_dump` backup
- Scheduled backup job
- Retention cleanup
- Restore documentation

Acceptance criteria:

- JSON export includes all required domain data.
- Import validates shape before writing.
- Backup files are written under `/backups`.
- Old backups are removed according to retention settings.

### Phase 11 - LLM-Assisted Entry & Localization

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

### Phase 12 - v1 Hardening

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
