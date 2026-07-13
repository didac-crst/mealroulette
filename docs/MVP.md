# MealRoulette MVP

This is the short implementation target. The full specification lives in `SPECS.md`.

## MVP Goal

Build a self-hosted app that lets a household enter recipes, manually or automatically plan lunch and dinner, generate shopping lists, receive Telegram reminders, cook from step-by-step recipe views, and recover household data from backups. LLM assistance can arrive after the manual flow is reliable.

## MVP Scope

### Must Have

- Docker Compose deployment with `api`, `worker`, `frontend`, and `db`.
- Automated unit tests for backend business logic.
- Automated integration tests for backend API endpoints.
- Pre-commit hook that runs the test suite before commits.
- CI workflow that runs the test suite on push and pull request.
- FastAPI backend with PostgreSQL.
- React + Vite frontend.
- Username/password login.
- Admin and user roles.
- Dishes, recipes, recipe steps, ingredients, ingredient aliases, units, and tags.
- Ingredient normalization flow.
- Weekly lunch/dinner meal plan.
- Manual meal assignment.
- Lock/unlock, mark eaten, skip, ate leftovers, generate week, reroll, and undo.
- Ratings.
- Shopping list generation for a selected date window.
- Compatible unit aggregation.
- Pantry-item exclusion.
- Telegram settings and manual test send.
- Daily Telegram reminder through APScheduler.
- Step-by-step cooking mode with timers.
- Basic automatic scheduler using explainable rules.
- JSON export/import.
- Mounted backup folder.
- Scheduled backups.

### Should Have

- Persisted shopping lists.
- PostgreSQL dump backup.

### Not in MVP

- Native mobile app.
- Nutrition tracking.
- Barcode scanning.
- Inventory tracking.
- Embedding-based scheduling.
- Vector database.
- Online recipe scraping.
- Complex multi-household permissions.

## First Build Slice

1. Bootstrap backend, frontend, database, Docker Compose, test harness, pre-commit, and CI. ✅
2. Add auth and users. ✅
3. Add catalog models and CRUD. ✅
4. Add dish library UI (login, dishes, recipes, steps, ingredients). ✅
5. Add meal plan models and manual planning. ✅
6. Add shopping list generation. ✅
7. Add Telegram reminders. ✅ ([`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0), PR #7)
8. Add automatic scheduling. ✅ ([`v0.5.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.5.0))
9. Add computed recipe traits and taxonomy. ✅ ([`v0.6.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.6.0), PR #9)
10. Add cooking mode. ✅ ([`v0.7.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.7.0), PR #10)
11. Add backup, export, and import. See [BACKUP_EXPORT_IMPORT.md](BACKUP_EXPORT_IMPORT.md).

## MVP Acceptance Test

A user can log in from a phone, create several dishes with normalized ingredients, plan lunch and dinner for the next three days, generate a shopping list, receive or manually send the list through Telegram, cook a recipe with step timers, mark meals as eaten, rate them, and export a restorable backup (Phase 11 — see [RESTORE.md](RESTORE.md)). Import into an empty database is supported for disaster recovery; merge into a live database is not.
