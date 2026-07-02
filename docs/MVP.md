# MealRoulette MVP

This is the short implementation target. The full specification lives in `SPECS.md`.

## MVP Goal

Build a self-hosted app that lets a household enter recipes, manually plan lunch and dinner, generate shopping lists, receive Telegram reminders, and cook from step-by-step recipe views. Automatic scheduling and LLM assistance can arrive after the manual flow is reliable.

## MVP Scope

### Must Have

- Docker Compose deployment with `api`, `worker`, `frontend`, and `db`.
- FastAPI backend with PostgreSQL.
- React + Vite frontend.
- Username/password login.
- Admin and user roles.
- Dishes, recipes, recipe steps, ingredients, ingredient aliases, units, and tags.
- Ingredient normalization flow.
- Weekly lunch/dinner meal plan.
- Manual meal assignment.
- Lock/unlock, mark cooked, skip, leftovers, reroll placeholder.
- Ratings.
- Shopping list generation for a selected date window.
- Compatible unit aggregation.
- Pantry-item exclusion.
- Telegram settings and manual test send.
- Daily Telegram reminder through APScheduler.
- JSON export/import.
- Mounted backup folder.

### Should Have

- Step-by-step cooking mode with timers.
- Persisted shopping lists.
- Scheduled backups.
- Basic automatic scheduler using explainable rules.

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

1. Bootstrap backend, frontend, database, and Docker Compose.
2. Add auth and users.
3. Add catalog models and CRUD.
4. Add meal plan models and manual planning.
5. Add shopping list generation.
6. Add Telegram reminders.
7. Add backups.
8. Add cooking mode.

## MVP Acceptance Test

A user can log in from a phone, create several dishes with normalized ingredients, plan lunch and dinner for the next three days, generate a shopping list, receive or manually send the list through Telegram, mark meals as cooked, rate them, and export a backup.
