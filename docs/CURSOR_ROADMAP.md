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
- Alembic revisions `004`–`010` add recipe difficulty, dish classification, recipe ownership, `is_main`, `image_url`, and simplified course enum — see root [README.md](../README.md#database-migrations-alembic).

### Phase 4 - Frontend Shell and Dish Library

**Status:** Done on branch `phase-4/frontend` (ready to merge for v0.1).

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

Deliverables:

- Meal plans
- Meal plan items
- Weekly plan API
- Current plan API
- Manual assignment
- Lock/unlock
- Mark cooked
- Skip
- Use leftovers
- Ratings
- Meal history events derived from item status changes

Acceptance criteria:

- User can plan lunch and dinner for a week manually.
- Locked items remain locked.
- Cooked/skipped/leftover state is stored and visible.
- Ratings affect stored dish/user rating records.

### Phase 6 - Shopping Lists

Deliverables:

- Dynamic shopping list generation
- Optional persisted shopping lists
- Shopping list items
- Shopping list generator calling `mealroulette.services.quantities` for aggregation
- Pantry filtering
- Category grouping
- Source meal references
- Shopping list UI

Acceptance criteria:

- Compatible units aggregate through base units.
- Incompatible units remain separate unless an ingredient-specific conversion exists.
- Shopping items show which planned meals require them.

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

### Phase 11 - LLM-Assisted Entry

Deliverables:

- Provider abstraction
- LLM settings
- Enrich dish endpoint
- Suggest ingredients endpoint
- Suggest tags endpoint
- Normalize ingredients endpoint
- Draft review UI

Acceptance criteria:

- LLM endpoints require authentication.
- LLM output is saved only after explicit user confirmation.
- Ingredient suggestions still pass through normalization flow.

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
