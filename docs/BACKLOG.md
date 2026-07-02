# MealRoulette Backlog

Execution tracker for what has been built, what is in progress, and what comes next.

This file is the **status board**. It does not replace the product spec or build plan:

- [SPECS.md](../SPECS.md) — product requirements and long-term version roadmap (v0.1 → v1.0)
- [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) — implementation phases (Phase 0 → Phase 12)
- [docs/MVP.md](MVP.md) — MVP scope and acceptance test

Update this file when a phase or version milestone lands.

---

## Current focus

**Phase 2 — Authentication and users**

Next deliverables:

- User model and migration
- Password hashing
- `POST /api/auth/login`, `logout`, `refresh`, `GET /api/auth/me`
- Role-based dependencies (`admin`, `user`)
- Initial admin bootstrap flow
- Unit and integration tests for auth

---

## Product roadmap (long term)

From [SPECS.md §17](../SPECS.md#17-mvp-roadmap). Versions describe *what the product can do*. Implementation phases below map to these releases.

| Version | Theme | Status |
| --- | --- | --- |
| **v0.1** | Foundation — backend, auth, catalog data, basic frontend | In progress |
| **v0.2** | Manual planning — weekly plan, meal actions, ratings, history | Not started |
| **v0.3** | Shopping list — generation, aggregation, pantry filter, UI | Not started |
| **v0.4** | Telegram reminders — settings, scheduled and manual send | Not started |
| **v0.5** | Automatic scheduler — explainable weekly generation, reroll | Not started |
| **v0.6** | LLM-assisted entry — draft enrichment, review before save | Not started |
| **v1.0** | Stable home version — mobile UI, backups, auth, scheduler, cooking mode | Not started |

### v0.1 — Foundation

- [x] FastAPI backend
- [x] PostgreSQL
- [x] Docker Compose
- [x] Unit and integration test harness
- [x] Pre-commit hook and CI test workflow
- [x] Basic frontend shell
- [ ] Users / auth
- [ ] Dishes
- [ ] Recipes
- [ ] Recipe steps
- [ ] Ingredients
- [ ] Ingredient aliases
- [ ] Units
- [ ] Tags
- [ ] Dish tags

### v0.2 — Manual Planning

- [ ] Weekly plan view
- [ ] Manual dish assignment
- [ ] Meal plan items
- [ ] Lock / unlock
- [ ] Mark cooked
- [ ] Skip
- [ ] Leftovers
- [ ] Meal history
- [ ] Ratings

### v0.3 — Shopping List

- [ ] Generate shopping list for next X days
- [ ] Aggregate compatible units
- [ ] Group by category
- [ ] Exclude pantry items
- [ ] Basic shopping list UI

### v0.4 — Telegram Reminders

- [ ] Telegram settings
- [ ] Send test message
- [ ] Daily scheduled reminder
- [ ] Shopping window config
- [ ] Manual send now

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
- [ ] Telegram reminders
- [ ] Recipe cooking mode

---

## Implementation phases

From [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md). Phases describe *how we build*. Several phases may be needed to complete one product version.

| Phase | Name | Maps to | Status |
| --- | --- | --- | --- |
| 0 | Project bootstrap | v0.1 | Done |
| 1 | Backend foundation | v0.1 | Done |
| 2 | Authentication and users | v0.1 | **Next** |
| 3 | Core catalog data | v0.1 | Not started |
| 4 | Frontend shell and dish library | v0.1 | Not started |
| 5 | Manual meal planning | v0.2 | Not started |
| 6 | Shopping lists | v0.3 | Not started |
| 7 | Telegram reminders | v0.4 | Not started |
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

### Phase 2 — Authentication and users

- [ ] User model
- [ ] Password hashing
- [ ] Login / logout / refresh / me endpoints
- [ ] Role-based dependencies
- [ ] Initial admin bootstrap flow
- [ ] Auth unit and integration tests

### Phases 3–12

See [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) for full deliverables and acceptance criteria per phase.

---

## Extras (outside phase plan)

| Item | Status | Commit |
| --- | --- | --- |
| Free ports before Docker Compose startup | Done | `31a84b0` |

---

## MVP checklist

Cross-reference for [docs/MVP.md](MVP.md). Checked items are done; the rest track the MVP acceptance test.

- [x] Docker Compose deployment
- [x] Automated unit and integration tests
- [x] Pre-commit and CI
- [x] FastAPI + PostgreSQL
- [x] React + Vite frontend (shell only)
- [ ] Username / password login
- [ ] Admin and user roles
- [ ] Dishes, recipes, ingredients, units, tags
- [ ] Ingredient normalization flow
- [ ] Weekly meal plan and manual assignment
- [ ] Meal actions (lock, cooked, skip, leftovers, reroll)
- [ ] Ratings
- [ ] Shopping list generation
- [ ] Telegram settings and reminders
- [ ] JSON export / import
- [ ] Mounted backup folder (directory exists; backup logic not yet implemented)

**MVP acceptance test** (not yet achievable): log in from a phone, create dishes, plan three days, generate a shopping list, send via Telegram, mark meals cooked, rate them, export a backup.

---

## How to update this file

1. When starting work, set **Current focus** to the active phase.
2. When a phase completes, mark it done, check off related version items, and add the commit hash.
3. When a product version (v0.1, v0.2, …) is fully shipped, update its row in the product roadmap table.
4. Do not duplicate spec detail here — link to `SPECS.md` and `CURSOR_ROADMAP.md` instead.
