# MealRoulette Backlog

Execution tracker for what has been built, what is in progress, and what comes next.

This file is the **status board**. It does not replace the product spec or build plan:

- [SPECS.md](../SPECS.md) — product requirements and long-term version roadmap (v0.1 → v1.0)
- [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) — implementation phases (Phase 0 → Phase 12)
- [docs/LOCALIZATION.md](LOCALIZATION.md) — multilingual content design (Phase 11; documented early, implement later)
- [docs/MVP.md](MVP.md) — MVP scope and acceptance test

Update this file when a phase or version milestone lands.

---

## Current focus

**Phase 7 shipped** as [`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0) (merge `a560e7a`, PR #7).

Next up: **Phase 8** — explainable automatic scheduler and meal reroll. See [CURSOR_ROADMAP.md](CURSOR_ROADMAP.md#phase-8---explainable-scheduler).

---

## Branch workflow

Use one branch per milestone, then merge via pull request:

- `phase-2/auth` — authentication and users (merged)
- `phase-3/catalog` — core catalog (merged)
- `phase-4/frontend` — dish library UI (merged in PR #3, `v0.1.0`)
- `phase-5/planning` — manual meal planning (merged in PR #4, `v0.2.0`)
- `phase-6/shopping` — shopping lists, ingredient catalog seed, ingredient admin UI (merged in PR #5, `v0.3.0`)
- `phase-7/telegram-review` — Telegram bot, reminders, on-demand commands, recipe links (merged in PR #7, `v0.4.0`)

---

## Product roadmap (long term)

From [SPECS.md §17](../SPECS.md#17-mvp-roadmap). **Versions** describe what users can do. **Phases** (below) are how we build them. A version is only *released* when all its phases are done — then tag `vX.Y.Z` per [RELEASES.md](RELEASES.md).

| Version | Theme | Status |
| --- | --- | --- |
| **v0.1** | Foundation — platform, auth, catalog (API + UI), basic frontend | **Done** ([`v0.1.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.1.0), merge `b41cdae`, PR #3) |
| **v0.2** | Manual planning — weekly plan, review flow, meal actions, ratings, lightweight leftovers | **Done** ([`v0.2.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.2.0), merge `fb20858`, PR #4) |
| **v0.3** | Shopping list — generation, aggregation, pantry filter, UI, ingredient catalog | **Done** ([`v0.3.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.3.0), merge `88d2675`, PR #5) |
| **v0.4** | Telegram reminders — settings, scheduled and manual send, bot commands | **Done** ([`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0), merge `a560e7a`, PR #7) |
| **v0.5** | Automatic scheduler — explainable weekly generation, reroll | Not started |
| **v0.6** | LLM-assisted entry — draft enrichment, review before save | Not started |
| **v1.0** | Stable home version — mobile UI, backups, auth, scheduler, cooking mode | Not started |

> **v0.4 shipped** as [`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0). Telegram bot commands, scheduled HTML reminders, recipe deep links, and admin settings. Release notes: [docs/releases/v0.4.0.md](releases/v0.4.0.md).

> **v0.2 shipped** as [`v0.2.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.2.0). Plan and review lunch/dinner for the week, record what was eaten, rate meals, and track lightweight leftovers. Release notes: [docs/releases/v0.2.0.md](releases/v0.2.0.md).

### v0.1 — Foundation

**Platform & tooling**

- [x] FastAPI backend
- [x] PostgreSQL
- [x] Docker Compose
- [x] Unit and integration test harness
- [x] Pre-commit hook and CI test workflow

**Auth (API)**

- [x] Users / auth
- [x] Admin and user roles

**Catalog (API — Phase 3)**

- [x] Dishes, recipes, recipe steps
- [x] Ingredients and ingredient aliases
- [x] Units and tags, dish tags
- [x] Ingredient normalization flow (resolve / confirm)

**Frontend (Phase 4)**

- [x] Login screen
- [x] Authenticated app layout (nav, protected routes)
- [x] Dish library (card grid, image URL or emoji placeholder)
- [x] Dish detail (read-only classification, recipe variant cards)
- [x] Dish add/edit (basic info, food profile tags, planning profile, seasonality)
- [x] Recipe variant add/edit (basics, ingredients, steps, main-recipe flag)
- [x] Ingredient resolve/confirm flow in recipe editor
- [x] Tag selection (protein, carb, style, temperature families)
- [ ] Dish library search and filters (spec filters — future polish)

### v0.2 — Manual Planning

- [x] Weekly plan view
- [x] Manual dish assignment (with main recipe auto-select)
- [x] Meal plan items (lunch + dinner, 7-day scaffold)
- [x] Lock / unlock
- [x] Mark eaten (ate as planned)
- [x] Skip (optional reason / comment)
- [x] Ate leftovers (lightweight — 7-day eaten-only sources, optional source picker)
- [x] Meal history API
- [x] Meal ratings (per meal slot, linked to dish/recipe)
- [x] Review flow (`review_saved_at`, needs-review filter)
- [x] Mobile polish (bottom tabs, review-first landing, touch-friendly actions)
- [ ] Reroll / roulette again (deferred to Phase 8 scheduler)

### v0.3 — Shopping List

- [x] Generate shopping list for next X days
- [x] Aggregate compatible units (including approved ingredient-specific conversions)
- [x] Group by category
- [x] Exclude pantry items
- [x] Basic shopping list UI (planned meals, `~` approximate totals, per-meal breakdown)
- [x] Ingredient seed catalog (`mealroulette_ingredients_seed.yaml` + `import_ingredient_seed`)
- [x] Per-ingredient unit behavior (family, preferred shopping unit, aggregation strategy)
- [x] Ingredient unit conversions with approval workflow (API + admin UI)
- [x] Ingredient admin dashboard (`/ingredients` list + edit)
- [x] Ingredient category reference + dropdown editor (`ingredient_categories.yaml`)

### v0.4 — Telegram Reminders

- [x] Telegram settings (admin UI + API)
- [x] Send test message
- [x] Daily scheduled reminder (APScheduler worker)
- [x] Shopping window config (days, include today, pantry, group by category)
- [x] Manual send now
- [x] Subscriber model (`/subscribe`, `/unsubscribe`)
- [x] On-demand bot commands (`/planning`, `/reminder`, `/shopping`)
- [x] HTML message formatting with safe truncation
- [x] Recipe deep links in planning (tap dish → ingredients + steps)
- [x] Send saved shopping list via Telegram

### v0.5 — Automatic Scheduler

- [ ] Weekly plan generation
- [ ] Weekly category targets
- [ ] Seasonality scoring
- [ ] Rating scoring
- [ ] Avoid recent dishes
- [ ] Similarity scoring
- [ ] Roulette again
- [ ] Selection reasons

### v0.6 — LLM-Assisted Entry

- [ ] LLM dish enrichment
- [ ] Suggest ingredients
- [ ] Suggest tags
- [ ] Suggest steps
- [ ] Suggest seasonality
- [ ] Review before save

### v1.0 — Stable Home Version

- [ ] Usable mobile UI
- [ ] Stable API
- [ ] Backup / restore
- [ ] Auth and roles
- [ ] Scheduler reliable enough for real use
- [x] Telegram reminders
- [ ] Recipe cooking mode

---

## Implementation phases

From [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md). Phases describe *how we build*. Several phases may be needed to complete one product version.

| Phase | Name | Maps to | Status |
| --- | --- | --- | --- |
| 0 | Project bootstrap | v0.1 | Done |
| 1 | Backend foundation | v0.1 | Done |
| 2 | Authentication and users | v0.1 | Done |
| 3 | Core catalog data | v0.1 | Done |
| 4 | Frontend shell and dish library | v0.1 | Done (PR #3, `v0.1.0`) |
| 5 | Manual meal planning | v0.2 | Done (PR #4, `v0.2.0`) |
| 6 | Shopping lists | v0.3 | Done (PR #5, `v0.3.0`) |
| 7 | Telegram reminders | v0.4 | Done (PR #7, `v0.4.0`) |
| 8 | Explainable scheduler | v0.5 | Not started |
| 9 | Cooking mode | v1.0 | Not started |
| 10 | Backup, export, and import | v1.0 | Not started |
| 11 | LLM-assisted entry | v0.6 | Not started |
| 12 | v1 hardening | v1.0 | Not started |

### Phase 0 — Project bootstrap ✅

Completed in `9f88c54`.

- [x] Docker Compose (`api`, `worker`, `frontend`, `db`)
- [x] FastAPI `/api/health`
- [x] React + Vite frontend shell with API health display
- [x] `.env.example`, developer commands
- [x] Pre-commit hooks and GitHub Actions CI
- [x] Initial backend and frontend tests

### Phase 1 — Backend foundation ✅

Completed in `9f88c54`.

- [x] SQLAlchemy 2.x setup
- [x] Alembic bootstrap migration
- [x] Config management (`pydantic-settings`)
- [x] Database session dependency
- [x] Predictable API error payloads
- [x] Test database fixture strategy
- [x] `/api/health/ready` database connectivity check

### Phase 2 — Authentication and users ✅

Completed on branch `phase-2/auth`.

- [x] User model and `002_users` migration
- [x] Password hashing (bcrypt) and JWT access/refresh tokens
- [x] Login / logout / refresh / me endpoints
- [x] Role-based dependencies (`admin`, `user`)
- [x] Admin user CRUD endpoints
- [x] Initial admin bootstrap command
- [x] Auth unit and integration tests

### Phase 3 — Core catalog data ✅

Merged in `815d67b` (PR #2).

- [x] Catalog models and `003_catalog` migration
- [x] Units, tags, ingredients, aliases, dishes, recipes, steps, seasonality
- [x] Catalog CRUD APIs (reads: any user; writes: admin)
- [x] Ingredient resolve / confirm flow (`create`, `map`, `alias`)
- [x] Reference data in YAML (`data/reference/units.yaml`, `tags.yaml`)
- [x] Idempotent seed CLI (`seed_reference_data`) on API startup after migrations
- [x] `services/quantities.py` — unit compatibility and aggregation rules (used by Phase 6)
- [x] Catalog integration tests

Design notes:

- **Reference data** lives in YAML, not Alembic data migrations. Re-running the seed only inserts missing rows.
- **Unit guardrails** are enforced in `services/quantities.py`, not in the spec. Shopping lists (Phase 6) must call `aggregate_by_ingredient()` rather than ad-hoc math.
- **Migrations `005`–`010`** extend catalog classification, recipe ownership, main recipe, image URL, and course enum (`004` is a no-op placeholder) — see [README.md](../README.md#database-migrations-alembic).

### Phase 4 — Frontend shell and dish library ✅

On branch `phase-4/frontend` (ready to merge).

- [x] Login, auth context, protected routes
- [x] Dish card library, detail, structured edit form
- [x] Separate recipe routes (view/edit), ingredients and steps
- [x] Dish vs recipe boundary: dish owns classification/planning; recipe owns preparation and times
- [x] Main recipe (`is_main`) drives displayed dish difficulty and prep/cook times
- [x] `thermomix_possible` derived from recipe variants (not edited on dish)
- [x] Seasonality: `all_year` or `seasonal` + preferred months only
- [x] Food profile tags: protein, carb, style, temperature (no cuisine, dietary, or dominant fields in UI)
- [x] Course: starter, main, or dessert

### Phase 5 — Manual meal planning ✅

Merged in `fb20858` (PR #4, `v0.2.0`).

- [x] Meal plans and plan items (migrations 011–014)
- [x] Planning API: current/week plan, assign dish/recipe, lock, mark eaten, skip, ate leftovers, reset, ratings
- [x] Lightweight leftovers: 7-day window, `eaten` sources only, no inventory
- [x] `review_saved_at` — needs-review filter until rating/skip/leftover source confirmed
- [x] Plan week UI and Review week UI with `MealSlotCard`
- [x] Mobile polish: bottom tab bar, review-first landing, compact week nav
- [x] Swagger OAuth2 token endpoint for `/docs`
- [x] Planning integration and unit tests

### Dev tooling — YAML fixtures

Supports local testing; distinct from Phase 10 full JSON export/import.

- [x] `sample_dishes.yaml` fixture format (symbolic tags, units, ingredient names)
- [x] `import_sample_dishes` CLI — idempotent import via catalog service
- [x] `mealroulette_ingredients_seed.yaml` — canonical ingredients, aliases, unit conversions
- [x] `import_ingredient_seed` CLI — idempotent ingredient catalog import (`--no-bootstrap-approve` to keep seed suggestions unapproved)

### Phase 6 — Shopping lists ✅

Merged in PR #5 (`v0.3.0`, commit `88d2675`).

Branch: `phase-6/shopping`.

- [x] Shopping list models and migrations (`015`–`016`)
- [x] Dynamic list generation from meal plans (date window)
- [x] Unit aggregation via `services/quantities` (strategy-aware, approved conversions only)
- [x] Pantry filtering and category grouping
- [x] Per-meal source contributions on list items
- [x] Shopping list API and UI (`/shopping`, nav tab **List**)
- [x] Ingredient unit behavior migration (`017`) — family, preferred shopping unit, aggregation unit/strategy
- [x] Ingredient seed import and conversion approval bootstrap
- [x] Ingredient conversions CRUD API (unique triplet constraint, migration `018`)
- [x] Ingredient admin UI — catalog list, edit aliases/conversions/unit behavior
- [x] Localization design documented ([LOCALIZATION.md](LOCALIZATION.md)); implementation deferred to Phase 11

### Phase 7 — Telegram reminders ✅

Branch: merged in PR #7 (`v0.4.0`).

- [x] Migration `019` — `telegram_settings`, `telegram_subscribers`
- [x] `TELEGRAM_BOT_TOKEN` + optional `TELEGRAM_BOT_USERNAME` in `.env` (api + worker)
- [x] Telegram settings API and admin UI (`/settings/telegram`)
- [x] Subscriber flow (`/subscribe`, `/unsubscribe`, `/help`)
- [x] On-demand commands: `/planning`, `/reminder`, `/shopping` (HTML, 1–14 days)
- [x] Recipe deep links in planning — tap dish → full recipe (ingredients + steps)
- [x] Daily scheduled reminder via APScheduler (`send_daily_reminder`)
- [x] Manual test + send-now endpoints; send saved shopping list
- [x] HTML formatters with safe truncation; shopping aggregation reused
- [x] Ingredient category reference + API + editor dropdown; seed import backfill
- [x] Logo assets in `frontend/public/`
- [x] Backend tests (telegram settings, API, reminder, formatters, updates, recipe links)

### Phases 8–12

See [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) for full deliverables and acceptance criteria per phase.

---

## Extras (outside phase plan)

| Item | Status | Commit |
| --- | --- | --- |
| Free ports before Docker Compose startup | Done | `31a84b0` |

## Future enhancements

Tracked ideas that are intentionally not in the current milestone plan:

### Passkeys (WebAuthn)

- **Goal:** optional passwordless sign-in from iPhone Safari using Face ID / Touch ID
- **When:** after login UI, HTTPS/domain setup, and normal mobile usage are working
- **Complexity:** medium — standard libraries exist (`py_webauthn`, `@simplewebauthn/browser`), but deployment needs TLS and a stable hostname
- **Approach:** add passkeys alongside username/password, not as the only auth method
- **Spec reference:** [SPECS.md §3.9](../SPECS.md#39-access-control)

---

## MVP checklist

Cross-reference for [docs/MVP.md](MVP.md). Checked items are done; the rest track the MVP acceptance test.

- [x] Docker Compose deployment
- [x] Automated unit and integration tests
- [x] Pre-commit and CI
- [x] FastAPI + PostgreSQL
- [x] React + Vite frontend with login and dish library
- [x] Dish list, detail, edit, recipe variants, steps, and ingredients (UI)
- [x] Username / password login (API)
- [x] Admin and user roles
- [x] Dishes, recipes, ingredients, units, tags (API)
- [x] Ingredient normalization flow (API)
- [x] Weekly meal plan and manual assignment
- [x] Meal actions (lock, eaten, skip, ate leftovers)
- [x] Ratings
- [ ] Meal reroll (deferred to Phase 8)
- [x] Shopping list generation
- [x] Telegram settings and reminders
- [ ] JSON export / import
- [ ] Mounted backup folder (directory exists; backup logic not yet implemented)

**MVP acceptance test** (partially achievable): log in from a phone, create dishes, plan three days, generate a shopping list, send via Telegram, mark meals eaten, rate them. **Still missing:** export a backup (Phase 10).

---

## How to update this file

1. When starting work, set **Current focus** to the active phase.
2. When a phase completes, mark it done, check off related version items, and add the merge commit hash.
3. When a **product version** (v0.1, v0.2, …) is fully shipped, update its row in the product roadmap table and create a `vX.Y.Z` tag — see [docs/RELEASES.md](RELEASES.md).
4. Do not duplicate spec detail here — link to `SPECS.md` and `CURSOR_ROADMAP.md` instead.
