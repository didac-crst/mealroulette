# Phase 11 handoff — taxonomy hardening before backup

## Document metadata

- **Purpose:** Phase 11 architecture handoff and blocking decisions (historical context).
- **Authority:** Historical — durable decisions live in ADRs and [features/backup-export-import.md](../features/backup-export-import.md).
- **Status:** Archived — Phase 11 shipped as v0.8.0.
- **Update when:** Do not update except to fix broken links.

---

Date: 2026-07-13  
Branch: `phase-11/taxonomy-backup`

## Context

`main` is at **v0.7.0**. The documented next milestone was Phase 11: backup, export, and import.

During architecture discussion, we decided that backup should **not** freeze the current transitional data model where:

- weekly scheduler targets still depend on `tags` / `dish_tags`;
- ingredient taxonomy is stored as string fields on `ingredients`;
- food groups and ingredient families are runtime YAML concepts rather than first-class database entities;
- recipe traits are computed from canonical ingredients but are not yet the source of truth for weekly target matching.

Full JSON export/import becomes a portable data contract — taxonomy and target semantics should be settled **before or together with** backup.

## Revised Phase 11 direction

```text
Phase 11 — Taxonomy hardening + backup, export, and import
```

Taxonomy hardening lands **before** finalizing the backup format.

See also:

- [ADR 002 — Canonical taxonomy and computed scheduler targets before backup contract](adr/002-canonical-taxonomy-before-backup.md)
- [../features/backup-export-import.md](../features/backup-export-import.md) (backup spec; prerequisites section)
- [../features/computed-traits.md](../features/computed-traits.md), [../features/taxonomy-resolver.md](../features/taxonomy-resolver.md), [../features/scheduler.md](../features/scheduler.md)

## Required architecture changes

### 1. Promote taxonomy to database tables

Add first-class tables:

- `food_groups`
- `ingredient_families`

Expected relationship:

```text
food_groups.id
ingredient_families.food_group_id -> food_groups.id
ingredients.family_id -> ingredient_families.id
```

Current string fields `ingredients.food_group` and `ingredients.family` become compatibility/migration concerns, not the long-term source of truth.

**Recommendation:** additive FK migration first, then switch reads/writes, then decide whether to drop old columns after compatibility tests.

### 2. Enforce canonical ingredients

Recipe ingredients must reference existing canonical `ingredients` rows. Unknown/free-text input goes through resolver flow (exact → fuzzy → human confirm → admin create with required taxonomy).

### 3. Migrate weekly target matching away from tags

`dish_matches_weekly_target` in `backend/mealroulette/services/scheduler/targets.py` should use computed traits / taxonomy for derivable targets (`fish`, `meat`, `pasta`, `rice`, `vegetarian`, …). Keep legacy tag fallback only during migration.

**`soup`** is not derivable from ingredients — needs explicit curated classification.

### 4. Redefine or retire tags

Do not keep generic tags as core scheduler truth after migration. Keep explicit curated classifications for non-derivable concepts (`soup`, `salad`, `quick`, …).

### 5. Backup format after taxonomy hardening

Export must include `food_groups`, `ingredient_families`, canonical ingredients, aliases, conversions, recipes with canonical refs, scheduler settings, and curated classifications if retained.

## Acceptance criteria (spec)

- Ingredient families and food groups are first-class domain concepts.
- Active ingredients cannot exist without valid taxonomy.
- Recipe ingredient persistence requires canonical ingredient IDs.
- Weekly target matching uses computed traits for derivable targets.
- Legacy tag fallback is explicitly temporary or removed.
- Non-derivable styles such as `soup` have an explicit curated representation.
- Full backup/export format reflects the hardened taxonomy model.
- Restore/import validates taxonomy referential integrity before writing.

## Delivered in branch

### Meal composition (catalog metadata)

- `meal_composition` / `simple_dish_part` on `dishes` — migration `027`, API, UI
- spec: [../features/meal-composition.md](../features/meal-composition.md)

### Taxonomy hardening

- `food_groups` and `ingredient_families` DB tables (migration `028`)
- `ingredients.family_id` FK with YAML seed + backfill (migration `030` — seed YAML + legacy family aliases)
- `TaxonomyService` reads from DB
- Ingredient create/update validates family against DB
- Weekly targets use computed traits first, tag fallback for non-derivable keys (`soup`, …)

### Dish classification UI

- Single source of truth on dish edit/detail: `meal_composition` for planner slots; main-recipe computed traits for fish/meat/pasta; curated `style` tags only for non-derivable cases (e.g. soup). See [../features/meal-composition.md](../features/meal-composition.md).

### Backup / export / import

- `backup_settings`, `backup_runs` (migration `029`)
- `GET /api/export/full`, `POST /api/import/full`, backup run/settings APIs
- Worker scheduled backup job (minute poll)
- Admin UI: Settings → Backups
- Export snapshots exclude in-flight `backup_runs`; `family_id` integrity validated after backfill
- Restore notes: [../operations/restore.md](../operations/restore.md)

### Other fixes

- Pydantic validation error handler serializes `model_validator` failures safely (`core/errors.py`)

Scheduler multi-component slots and pairing logic remain future work.

## Open product decisions

- Exact **vegetarian** semantics (meat/fish/seafood only vs egg/dairy; separate vegan?).
- Whether **`fish`** target includes seafood.
- Whether **`soup`** is dish-level, recipe-level, or classification table data.
- Whether existing **`tags`** table is retired or repurposed.
- Whether old string taxonomy columns are dropped in Phase 11 or kept one release for compatibility.
