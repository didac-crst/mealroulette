# MealRoulette Backlog

Execution tracker for what has been built, what is in progress, and what comes next.

This file is the **status board**. It does not replace the product spec or build plan:

- [SPECS.md](../SPECS.md) — product requirements and long-term version roadmap (v0.1 → v1.0)
- [docs/CURSOR_ROADMAP.md](CURSOR_ROADMAP.md) — implementation phases (Phase 0 → Phase 13)
- [docs/LOCALIZATION.md](LOCALIZATION.md) — multilingual content design (Phase 12; documented early, implement later)
- [docs/MVP.md](MVP.md) — MVP scope and acceptance test

Update this file when a phase or version milestone lands.

---

## Current focus

**Phase 11 — Taxonomy hardening + backup** on branch `phase-11/taxonomy-backup` (from `v0.7.0`).

Taxonomy and scheduler target semantics must settle **before** the JSON backup contract is finalized. See [PHASE11_HANDOFF.md](PHASE11_HANDOFF.md), [ADR 002](adr/002-canonical-taxonomy-before-backup.md), and [BACKUP_EXPORT_IMPORT.md](BACKUP_EXPORT_IMPORT.md).

**v0.7 shipped** as [`v0.7.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.7.0) — Today home, cooking mode, step timers, Telegram cooking alerts, dish search. Release notes: [docs/releases/v0.7.0.md](releases/v0.7.0.md).

---

## Technical debt watchlist

Track these as opportunistic refactors, not a standalone rewrite. Prefer tackling them when the affected area is already changing for a feature or bug fix.

- [ ] Add CI gates for frontend build/typecheck and backend lint/format, not only test execution.
- [ ] Split large frontend page components into smaller form sections, data-loading hooks, validation helpers, and reusable controls:
  - `frontend/src/features/dishes/RecipeEditPage.tsx`
  - `frontend/src/features/ingredients/IngredientEditPage.tsx`
  - `frontend/src/features/planning/MealSlotCard.tsx`
- [ ] Break up large backend services by separating read/query helpers, mutation workflows, serialization helpers, and domain rules:
  - `backend/mealroulette/services/catalog.py`
  - `backend/mealroulette/services/shopping.py`
- [ ] Split `frontend/src/styles/app.css` into feature-level or component-level style files once UI changes become frequent.
- [ ] Strengthen frontend coverage around edit forms, planning flows, and shopping list behavior.

---

## Branch workflow

Use one branch per milestone, then merge via pull request:

- `phase-2/auth` — authentication and users (merged)
- `phase-3/catalog` — core catalog (merged)
- `phase-4/frontend` — dish library UI (merged in PR #3, `v0.1.0`)
- `phase-5/planning` — manual meal planning (merged in PR #4, `v0.2.0`)
- `phase-6/shopping` — shopping lists, ingredient catalog seed, ingredient admin UI (merged in PR #5, `v0.3.0`)
- `phase-7/telegram-review` — Telegram bot, reminders, on-demand commands, recipe links (merged in PR #7, `v0.4.0`)
- `phase-8/scheduler` — explainable scheduler, family-vector similarity, scheduled roulette (merged, `v0.5.0`, PR #8)
- `phase-9/computed-recipe-traits` — public keys, food groups, computed recipe traits, taxonomy & resolver (merged in PR #9, `v0.6.0`)
- `phase-10/cooking-mode` — interactive cooking mode with step timers & Telegram alerts (PR #10)

---

## Product roadmap (long term)

From [SPECS.md §17](../SPECS.md#17-mvp-roadmap). **Versions** describe what users can do. **Phases** (below) are how we build them. A version is only *released* when all its phases are done — then tag `vX.Y.Z` per [RELEASES.md](RELEASES.md).

| Version | Theme | Status |
| --- | --- | --- |
| **v0.1** | Foundation — platform, auth, catalog (API + UI), basic frontend | **Done** ([`v0.1.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.1.0), merge `b41cdae`, PR #3) |
| **v0.2** | Manual planning — weekly plan, review flow, meal actions, ratings, lightweight leftovers | **Done** ([`v0.2.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.2.0), merge `fb20858`, PR #4) |
| **v0.3** | Shopping list — generation, aggregation, pantry filter, UI, ingredient catalog | **Done** ([`v0.3.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.3.0), merge `88d2675`, PR #5) |
| **v0.4** | Telegram reminders — settings, scheduled and manual send, bot commands | **Done** ([`v0.4.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.4.0), merge `a560e7a`, PR #7) |
| **v0.5** | Automatic scheduler — explainable weekly generation, reroll | **Done** ([`v0.5.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.5.0)) |
| **v0.6** | Catalog keys & computed traits — public keys, food groups, recipe trait metadata | **Done** ([`v0.6.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.6.0), merge `322c30c`, PR #9) |
| **v0.7** | Cooking mode — Today home, step-by-step cooking, timers, dish search | **Done** ([`v0.7.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.7.0), merge `9f8fe92`, PR #10) |
| **v0.8** | LLM-assisted entry — draft enrichment, review before save | Not started |
| **Future** | Composable meals — complete / half / dessert roles, paired halves, manual desserts | Backlog only (see below) |
| **v1.0** | Stable home version — backups, auth hardening, scheduler reliability | Not started |

> **v0.6 shipped** as [`v0.6.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.6.0). Catalog keys, computed traits, taxonomy APIs, resolver, taxonomy navigator UI. Release notes: [docs/releases/v0.6.0.md](releases/v0.6.0.md).

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
- [x] Dish library search (client-side name / recipe variant filter)
- [ ] Dish library filters (tags, course — future polish)

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
- [x] Mobile polish (bottom tabs, today-first landing (Phase 10), touch-friendly actions)
- [x] Reroll / roulette again (Phase 8 scheduler)

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

- [x] Planning rules + weekly targets with tolerance
- [x] Family-vector similarity ([SCHEDULER.md](SCHEDULER.md): on-the-fly L1 %, count fallback 100 g, cosine distance)
- [x] History-aware scoring (temporal neighbours: eaten + planned + in-run picks)
- [x] Seasonality + rating scoring
- [x] Generate week (unlocked slots only; locked preserved)
- [x] Reroll one meal (today and future only)
- [x] Undo last roulette action
- [x] Meal swap (manual rebalance, no scoring)
- [x] Plan dish from gallery (calendar day + lunch/dinner)
- [x] Selection reasons on auto-picked items
- [x] Plan UI: generate week, reroll, undo, swap, reasons display
- [x] Scheduled roulette worker job + admin settings UI (`/settings/scheduler`)
- [x] Telegram “New roulette” notification (configurable planning days)

### v0.6 — Catalog Keys & Computed Traits

**Branch:** `phase-9/computed-recipe-traits`. Must remain compatible with v0.5 scheduler, weekly targets UI, shopping, planning, and Telegram.

**Additive first:** computed traits are a parallel metadata layer. Weekly target matching (`fish`, `meat`, `pasta`, `rice`, `vegetarian`, `soup`) keeps using **dish tags** until an explicit later migration step with tests.

- [x] Document Phase 9 spec (`docs/COMPUTED_TRAITS.md`, `docs/TAXONOMY_AND_RESOLVER.md`)
- [x] Taxonomy YAML split under `backend/mealroulette/data/taxonomy/` + loader validation
- [x] Migration: `ingredients.food_group`, `dishes.public_key`, `recipes.public_key`, `recipes.sequence_number`, `recipes.computed_traits_json`
- [x] Backfill food groups from category mapping; backfill public keys and recipe sequences; compute traits
- [x] Stable dish public keys (`<slug>-<random>`, length 32, immutable on rename)
- [x] Stable recipe public keys (`<dish_public_key>-001`, min 3-digit sequence; grows for 1000+)
- [x] Ingredient food-group vocabulary + centralized category→group mapping module
- [x] Recipe trait computation service (family vector, food groups, vegan, carb_heavy, dominant carb/protein)
- [x] Explicit trait refresh on recipe/ingredient/conversion changes
- [x] API: expose `food_group`, `public_key`, `computed_traits_json` on ingredients, dishes, recipes, meal-plan items
- [x] Dish effective traits = main recipe traits; meal-plan item = selected recipe traits (or main recipe fallback)
- [x] Scheduler: add `computed_traits_json` to `DishCandidate`; **do not** replace `dish_matches_weekly_target` in first pass
- [x] Ingredient resolver (exact/alias/fuzzy) + taxonomy browsing APIs — see [TAXONOMY_AND_RESOLVER.md](TAXONOMY_AND_RESOLVER.md)
- [x] Frontend: TypeScript types, ingredient food-group field, trait display, taxonomy navigator (`/ingredients/taxonomy`)
- [x] Tests: key generation, trait rules, migration backfill, resolver, taxonomy API, scheduler/weekly-target regression
- [x] Release notes `v0.6.0.md`

**Out of scope for v0.6 initial pass (later explicit steps):**

- [ ] Migrate weekly target matching from tags to computed traits (with opt-in fallback + mapping tests)
- [ ] Remove dish tags or tag editor
- [ ] Trait-based Telegram output
- [ ] Configurable trait thresholds (hard-code `CARB_HEAVY_THRESHOLD_PCT = 33.0` for now)

**Catalogue expansion (post–v0.6, proposal-driven):**

- [x] Import expanded taxonomy **proposals** under `data/taxonomy/proposals/` (627 candidates — not active truth)
- [x] Document MVP target 500–700 ingredients — [docs/taxonomy/catalogue_assessment_and_mvp_plan.md](taxonomy/catalogue_assessment_and_mvp_plan.md)
- [x] ADR 001 taxonomy contract — [docs/adr/001-ingredient-taxonomy-contract.md](adr/001-ingredient-taxonomy-contract.md)
- [x] Deterministic validator + exception report — `make validate-taxonomy`
- [x] Reconcile active seed — **412 ingredients**, **0 blockers** — [docs/taxonomy/RECONCILIATION_LOG.md](taxonomy/RECONCILIATION_LOG.md)
- [x] Migration `023` — `storage_class`, `culinary_category`, `product_form`, `preservation`
- [x] Migration `024` — `storage_after_opening`, `traits_json`
- [x] Migration `025` — widen `recipes.public_key` for long sequence suffixes
- [x] Human review batch — 17 active ingredients resolved (see [RECONCILIATION_LOG.md](taxonomy/RECONCILIATION_LOG.md))
- [x] CodeRabbit review findings addressed (PR #9)
- [ ] Re-import reconciled seed into running DB (`import_ingredient_seed` after deploy)
- [ ] LLM semantic validation batches — [llm_taxonomy_review_prompt.md](taxonomy/llm_taxonomy_review_prompt.md)
- [ ] Recipe-driven validation (≥95% auto-resolve target)
- [ ] Promote remaining reviewed proposal rows in batches when evidence supports

### v0.7 — Cooking mode

- [x] Today home (`/today`) with Cook + Review
- [x] Cooking mode route and step navigation
- [x] Step timers with browser chime and Telegram alerts
- [x] Dish library real-time search
- [x] Release notes [`v0.7.0.md`](releases/v0.7.0.md)

### v0.8 — LLM-Assisted Entry

- [ ] LLM dish enrichment
- [ ] Suggest ingredients
- [ ] Suggest tags
- [ ] Suggest steps
- [ ] Suggest seasonality
- [ ] Review before save

### Future — composable meals (meal composition)

**Status:** Catalog metadata implemented in Phase 11 (`meal_composition`, `simple_dish_part` on `dishes`). Scheduler pairing and multi-component slots remain backlog.

See [MEAL_COMPOSITION.md](MEAL_COMPOSITION.md).

| Composition | Scheduler | Example |
| --- | --- | --- |
| **`main_dish`** | Auto-assignable as the sole dish for a lunch/dinner slot | Mushroom risotto |
| **`simple_dish`** | Auto-assignable only as **one of two** components in the same slot | Beans & potatoes; ham croquettes |
| **`dessert`** | **Manual assign only** — never picked by roulette | Fruit crumble |

When `meal_composition = simple_dish`, **`simple_dish_part`** is required: `centerpiece` or `sidedish`.

**Product rules (draft):**

- A lunch/dinner slot is satisfied by either **1× main_dish** or **2× simple_dish** (centerpiece + sidedish).
- Do **not** model “beans + croquettes” as a single synthetic dish — keep real dishes separate.
- Desserts may appear on the plan but are **excluded from** auto generation.
- Half-meal pairing should prefer variety/compatibility (rules TBD).

**Checklist (when scheduled):**

- [x] Data model: `meal_composition` + `simple_dish_part` on `dishes` (migration `027`, catalog UI).
- [ ] **Multi-component slots:** `MealPlanItem` currently has one `dish_id` / `recipe_id` per slot — need components without breaking the unique `(plan, date, meal_slot)` constraint.
- [ ] Scheduler: candidate generation for main vs compatible simple-dish pairs; desserts filtered out of auto pool.
- [ ] Weekly targets: count **per slot** (one fish dinner), not per component — document edge cases.
- [ ] Similarity / vectors: score pairs (or each half vs neighbours); avoid double-counting same slot in neighbour logic.
- [ ] Shopping list: aggregate ingredients from **all** components in a slot.
- [ ] Plan UI: show two lines per slot when composed; swap/reroll semantics (reroll pair? one half?).
- [ ] Telegram / cooking mode: display multiple dishes per slot.
- [ ] Map legacy `course=starter` → half meal or drop starter enum (product decision).

**Open questions:**

- Manual “add second half” on an existing slot vs scheduler-only pairing?
- Can a half meal be promoted to complete for simple weeks (catalog convenience)?
- Rating: one rating per slot or per component?

### v1.0 — Stable Home Version

- [ ] Usable mobile UI
- [ ] Stable API
- [ ] Backup / restore
- [ ] Auth and roles
- [ ] Scheduler reliable enough for real use
- [x] Telegram reminders
- [x] Recipe cooking mode (Phase 10, PR #10)
- [x] Today home with Cook / Review entry (Phase 10, PR #10)

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
| 8 | Explainable scheduler | v0.5 | Done (`v0.5.0`) |
| 9 | Computed recipe traits & catalog keys | v0.6 | Done (PR #9, `v0.6.0`) |
| 10 | Cooking mode | v0.7 | Done (PR #10, `v0.7.0`) |
| 11 | Taxonomy hardening + backup, export, import | v1.0 | Ready for PR (`phase-11/taxonomy-backup`) |
| 12 | LLM-assisted entry & localization | v0.8 | Not started |
| 13 | v1 hardening | v1.0 | Not started |

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
- [x] Mobile polish: bottom tab bar, today-first landing (Phase 10), compact week nav
- [x] Swagger OAuth2 token endpoint for `/docs`
- [x] Planning integration and unit tests

### Dev tooling — YAML fixtures

Supports local testing; distinct from Phase 11 full JSON export/import.

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
- [x] Localization design documented ([LOCALIZATION.md](LOCALIZATION.md)); implementation deferred to Phase 12

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

### Phase 8 — Explainable scheduler ✅

Shipped as [`v0.5.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.5.0). Full plan: [CURSOR_ROADMAP.md § Phase 8](CURSOR_ROADMAP.md#phase-8---explainable-scheduler). Vector math: [SCHEDULER.md](SCHEDULER.md).

- [x] Migration `020` — `planning_rules`, `scheduler_settings`
- [x] Migration `021` — `meal_plans.last_roulette_undo_json`
- [x] Family vector builder + cosine similarity + unit tests
- [x] Scoring engine + 50-attempt generator + temporal neighbours
- [x] `SchedulerService` — generate week, reroll, undo
- [x] API: generate/reroll/undo/swap/assign + planning rules + scheduler settings
- [x] Plan UI: generate, reroll, undo, swap, selection reasons, plan-from-gallery
- [x] Scheduled roulette worker + `ScheduledRouletteService`
- [x] Telegram “New roulette” notification
- [x] Admin UI `/settings/scheduler`
- [x] Settings hub (`/settings`), weekly targets UI, household timezone clock
- [x] Acceptance API tests + release notes `v0.5.0.md`

### Phase 9 — Computed recipe traits & catalog keys ✅

Shipped in `v0.6.0` via PR #9. Full plan: [CURSOR_ROADMAP.md § Phase 9](CURSOR_ROADMAP.md#phase-9---computed-recipe-traits--catalog-keys). Specs: [COMPUTED_TRAITS.md](COMPUTED_TRAITS.md), [TAXONOMY_AND_RESOLVER.md](TAXONOMY_AND_RESOLVER.md).

**Authoritative taxonomy files** (not the superseded single-YAML proposal):

- `backend/mealroulette/data/taxonomy/food_groups.yaml`
- `backend/mealroulette/data/taxonomy/ingredient_families.yaml`
- `backend/mealroulette/data/taxonomy/batch_plan.yaml`

**Ingredient seed (single file):** `backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml` — validated against taxonomy on import. The duplicate `taxonomy/ingredients_seed.yaml` and embedded `ingredient_families` block in the fixtures file were removed.

- [x] Migration `022`–`025` + backfill (food groups, public keys, recipe sequences, computed traits, taxonomy metadata)
- [x] Public key generation services + tests
- [x] Food group mapping module + ingredient API/UI
- [x] Recipe trait computation + refresh hooks
- [x] Effective traits on dishes and meal-plan items (API)
- [x] Scheduler candidate carries `computed_traits_json` (tags unchanged for weekly targets)
- [x] Frontend types + trait display on dish/recipe detail; food group on ingredient edit/detail
- [x] Regression: scheduler acceptance, weekly targets settings, shopping unchanged
- [x] Ingredient resolver (exact/alias/fuzzy/classify-candidate) + taxonomy browsing APIs
- [x] Taxonomy navigator UI (`/ingredients/taxonomy`)
- [x] Release notes `v0.6.0.md`
- [x] Validation: `make test-backend` (189 passed, 2 skipped), frontend 18 passed, `npm run build` green; `make validate-taxonomy` — 0 blockers

### Phase 10 — Cooking mode ✅

Branch: `phase-10/cooking-mode`. Spec: [COOKING_MODE.md](COOKING_MODE.md). Merged PR [#10](https://github.com/didac-crst/mealroulette/pull/10), tag [`v0.7.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.7.0), merge `9f8fe92`.

- [x] Phase 10 spec (`docs/COOKING_MODE.md`)
- [x] **`/today` home** — default route; lunch/dinner cards with Cook + Review
- [x] Route `/recipes/:recipeId/cook` + `RecipeCookingPage`
- [x] **Cook** button on recipe detail
- [x] Previous / Next step navigation (local state)
- [x] Collapsible full ingredient list
- [x] Step countdown timers (optional minutes per step in recipe edit)
- [x] Telegram alert when cooking timer ends (subscribers; worker)
- [x] Browser timer chime + dismiss-at-zero UX
- [x] Dish library real-time search (client-side)
- [x] Frontend tests (navigation, boundaries, no-step fallback)
- [x] Manual mobile QA
- [x] Merge PR and tag [`v0.7.0`](https://github.com/didac-crst/mealroulette/releases/tag/v0.7.0)

Deferred (not first pass): Thermomix layout, persistent sessions, Telegram entry.

**PR [#10](https://github.com/didac-crst/mealroulette/pull/10) review follow-ups (CodeRabbit, 2026-07-12)** — tracked so deferred items are not lost:

- [ ] **Worker:** commit each cooking timer alert immediately after send/update in `process_due` (one failure must not block the rest)
- [ ] **Test:** `test_process_due` failure path when Telegram `send_message` raises (assert `failed` status + `last_error`)
- [ ] **Frontend:** batch or bundled recipe variant names for dish search (replace per-dish `fetchRecipes` in `DishListPage` when catalog grows)
- [ ] **Frontend:** surface save/add errors in `RecipeEditPage` step editor (catch API failures instead of silent `finally`-only)
- [ ] **Refactor:** dedupe action buttons in `CookingStepTimer` compact vs full layout
- [ ] **Docs:** vary acceptance-criteria wording in `CURSOR_ROADMAP.md` Phase 10 (cosmetic)
- [ ] **Repo:** docstring coverage threshold (CodeRabbit pre-merge warning; not Phase 10-specific)

Addressed in PR #10 commit `cee1ae0`: Telegram schedule/cancel race, today Review without dish, timer label helper, BACKLOG wording, timer tick side effects, test mocks.

### Phases 11–13

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
- [x] Meal reroll (generate week, reroll, undo — Phase 8)
- [x] Shopping list generation
- [x] Telegram settings and reminders
- [x] JSON export / import (Phase 11 — admin API, scheduled backups, restore docs)
- [x] Mounted backup folder (`./backups` volume; retention cleanup)

**MVP acceptance test:** log in from a phone, create dishes, plan three days, generate a shopping list, send via Telegram, mark meals eaten, rate them, and export a restorable JSON backup (admin → Backups or `GET /api/export/full`). Optional `pg_dump` when enabled in backup settings.

---

## How to update this file

1. When starting work, set **Current focus** to the active phase.
2. When a phase completes, mark it done, check off related version items, and add the merge commit hash.
3. When a **product version** (v0.1, v0.2, …) is fully shipped, update its row in the product roadmap table and create a `vX.Y.Z` tag — see [docs/RELEASES.md](RELEASES.md).
4. Do not duplicate spec detail here — link to `SPECS.md` and `CURSOR_ROADMAP.md` instead.
