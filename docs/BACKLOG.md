# MealRoulette Backlog

Execution tracker for what has been built, what is in progress, and what comes next.

This file is the **status board**. It does not replace the product spec or build plan:

- [SPECS.md](../SPECS.md) — product requirements and long-term version roadmap (v0.1 → v1.0)
- [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) — implementation phases (Phase 0 → Phase 12)
- [docs/MVP.md](MVP.md) — MVP scope and acceptance test

Update this file when a phase or version milestone lands.

---

## Current focus

**Phase 3 — Core catalog data** (branch `phase-3/catalog`, in progress)

Implemented on branch; pending commit and PR:

- Catalog models, `003_catalog` migration, CRUD APIs
- Ingredient resolve / confirm flow
- Reference data in YAML (`units.yaml`, `tags.yaml`), idempotent seed on API startup
- `services/quantities.py` — unit compatibility and aggregation rules (foundation for Phase 6 shopping lists)

---

## Branch workflow

Use one branch per milestone, then merge via pull request:

- `phase-2/auth` — authentication and users
- `phase-3/catalog` — core catalog (in progress)

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
- [x] Users / auth
- [x] Dishes
- [x] Recipes
- [x] Recipe steps
- [x] Ingredients
- [x] Ingredient aliases
- [x] Units
- [x] Tags
- [x] Dish tags

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
| 2 | Authentication and users | v0.1 | Done |
| 3 | Core catalog data | v0.1 | In progress |
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

### Phase 2 — Authentication and users ✅

Completed on branch `phase-2/auth`.

- [x] User model and `002_users` migration
- [x] Password hashing (bcrypt) and JWT access/refresh tokens
- [x] Login / logout / refresh / me endpoints
- [x] Role-based dependencies (`admin`, `user`)
- [x] Admin user CRUD endpoints
- [x] Initial admin bootstrap command
- [x] Auth unit and integration tests

### Phase 3 — Core catalog data 🚧

In progress on branch `phase-3/catalog`.

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

### Phases 4–12

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
- [x] React + Vite frontend (shell only)
- [x] Username / password login
- [x] Admin and user roles
- [x] Dishes, recipes, ingredients, units, tags
- [x] Ingredient normalization flow
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
