# Computed Traits and Catalog Keys

## Document metadata

- **Purpose:** Public keys, food groups, computed recipe traits, and scheduler compatibility rules.
- **Authority:** Canonical for trait computation semantics; taxonomy structure defers to [taxonomy-resolver.md](taxonomy-resolver.md).
- **Status:** Living — update when trait keys or computation rules change.
- **Update when:** `computed_traits` services or catalog keys change.

---

Source of truth for public keys, ingredient food groups, computed recipe traits, and backward-compatibility rules with the scheduler.

See also: [CURSOR_ROADMAP.md](../CURSOR_ROADMAP.md) § Phase 9, [scheduler.md](scheduler.md) (family vectors for similarity — separate from traits metadata).

## Goals

1. **Stable public keys** for dishes and recipes (immutable identifiers for URLs, exports, and future integrations).
2. **Ingredient food groups** — a controlled vocabulary derived from category with optional override.
3. **Computed recipe traits** — JSON metadata derived from recipe ingredients (family vector, food-group weights, vegan, carb-heavy, dominant carb/protein).
4. **Additive compatibility** — weekly target matching, dish tags, shopping lists, and Telegram output remain unchanged in the first implementation pass.

## Backward compatibility (critical)

### Dish tags

Keep `tags`, `dish_tags`, tag editor, and `DishCandidate.tag_names` / protein / carb / style tag sets. Do **not** remove tags in Phase 9.

### Weekly targets

The scheduler matches weekly targets (`fish`, `meat`, `vegetarian`, `pasta`, `rice`, `soup`) via **dish tags** today. Phase 9 must **not** replace `dish_matches_weekly_target` in the first pass.

Computed traits are added in parallel on `DishCandidate.computed_traits_json` for future migration only.

Optional later step (explicit tests required):

```text
if target matches old tags → match
else if target maps cleanly to computed trait → match
else → no match
```

Preset → trait mapping (future only):

| Preset | Trait fallback (if enabled) |
| --- | --- |
| `fish` | food group `fish` or `seafood` |
| `meat` | food group `meat` |
| `vegetarian` | `vegan` true, or no meat/fish/seafood (product decision) |
| `pasta` | `dominant_carb` = `pasta_family` or family vector contains `pasta_family` |
| `rice` | `dominant_carb` = `rice_family` or family vector contains `rice_family` |
| `soup` | **tag/style only** — not derivable from food groups |

### Shopping list & Telegram

Computed traits do not affect ingredient aggregation or message formatting in Phase 9.

## Public keys

Integer primary keys remain internal. Public keys are separate unique columns.

### Constants

```text
DISH_PUBLIC_KEY_LENGTH = 32
DISH_PUBLIC_KEY_MAX_SLUG_LENGTH = 20
DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH = 8
RECIPE_SEQUENCE_WIDTH = 3
PUBLIC_KEY_ALPHABET = 0123456789abcdefghjkmnpqrstvwxyz
```

### Dish public key

Format: `<slug>-<random_suffix>`

- Total length exactly **32**.
- Slug from dish name at creation (lowercase alphanumeric, max 20 chars).
- Random suffix fills remainder (minimum 8 chars).
- Generated **once**; **does not change** when the dish is renamed.
- Globally unique.

### Recipe public key

Format: `<dish_public_key>-001`

- Sequence width **3 minimum** (`001`, `002`, …); width grows for `1000+`.
- Unique per dish (`recipes.dish_id` + `sequence_number`).
- Total public key length is normally **36**, with database capacity up to **40** for long sequence suffixes.

### Sequence ordering (backfill and new recipes)

1. Main recipe first (`is_main = true`), lowest id if multiple mains.
2. Remaining recipes by ascending `recipe.id`.

## Ingredient food groups

Column: `ingredients.food_group`.

**Source of truth:** [backend/mealroulette/data/taxonomy/food_groups.yaml](../backend/mealroulette/data/taxonomy/food_groups.yaml) loaded via `mealroulette.data.taxonomy_loader`.

**Ingredient families:** [ingredient_families.yaml](../backend/mealroulette/data/taxonomy/ingredient_families.yaml) — used for similarity vectors (`ingredient.family`), dominant carb/protein, and top-down resolution.

See [taxonomy-resolver.md](taxonomy-resolver.md) for the full taxonomy design, resolver strategy, and batch growth plan.

### Vocabulary (summary)

```text
vegetable, carbohydrate, meat, fish, seafood, egg, dairy, cheese, legume,
plant_protein, fat, condiment, herb, spice, stock, fruit, fungus, alcohol,
pantry, other
```

Module: `mealroulette.services.food_groups`.

### Category → food group (default mapping)

| Category | Food group |
| --- | --- |
| vegetable | vegetable |
| grain, pasta, bread, pastry, potato | carbohydrate |
| meat | meat |
| fish | fish |
| seafood | seafood |
| egg | egg |
| dairy | dairy |
| cheese | cheese |
| legume | legume |
| plant_protein | plant_protein |
| fruit | fruit |
| fungus | fungus |
| condiment | condiment |
| herb | herb |
| spice | spice |
| stock | stock |
| alcohol | alcohol |
| pantry, canned, preserved | pantry |
| frozen | other |
| unknown | other |

Explicit `food_group` on an ingredient **overrides** category inference.

## Computed recipe traits

Column: `recipes.computed_traits_json` (JSONB).

### Shape

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

### Computation rules

- Include all recipe ingredients in percentage-based vectors and trait flags.
- Omit lines below **`vector_min_grams`** (default **5 g**) after unit conversion — this keeps pinches of salt, spices, and similar amounts from affecting percentages.
- Use the same gram/ml conversion rules as scheduler family vectors (`family_vector.py`).
- `family_vector`: L1-normalized weights (percentages) by ingredient `family`, with category/canonical fallback (same as scheduler).
- `food_group_weights`: L1-normalized weights by resolved food group.
- `contains_food_groups`: food groups with non-zero weight after normalization.
- `vegan = false` if any ingredient has food group in `{meat, fish, seafood, egg, dairy, cheese}`; else `true`.
- `contains_meat = true` only for food group `meat` (fish/seafood are not meat).
- `carb_heavy = true` when carbohydrate percentage ≥ **33.0** (`CARB_HEAVY_THRESHOLD_PCT`, hard-coded).
- `dominant_carb`: highest gram weight among **carbohydrate** ingredients, keyed by ingredient family (with fallback).
- `dominant_protein`: highest gram weight among `{meat, fish, seafood, egg, dairy, cheese, legume, plant_protein}` families.

Do **not** infer style tags (e.g. `soup`) from ingredients in Phase 9.

Module: `mealroulette.services.recipe_traits`.

### Trait refresh

Refresh `computed_traits_json` when:

- recipe ingredient added, updated, or deleted;
- ingredient `category`, `food_group`, `family`, or `pantry_item` changes;
- approved unit conversion affecting recipe quantities changes.

Prefer explicit service-level refresh (catalog mutations call refresh helpers).

## Effective traits (read model)

| Entity | Source |
| --- | --- |
| `DishPublic.computed_traits_json` | Main recipe traits |
| `MealPlanItemPublic.computed_traits_json` | Selected recipe traits if `recipe_id` set; else dish main recipe traits |

Display/filter metadata only — assignment semantics unchanged.

### UI

- **Recipe detail** — food group composition donut chart from `RecipePublic.computed_traits_json` (computed on read).
- **Dish detail** — same chart from `DishPublic.computed_traits_json` (main recipe traits).

## API fields

| Schema | New fields |
| --- | --- |
| `IngredientPublic` / create / update | `food_group`, `storage_class`, `storage_after_opening`, `culinary_category`, `product_form`, `preservation`, `traits_json` |
| `DishPublic` | `public_key`, `computed_traits_json` |
| `RecipePublic` | `public_key`, `sequence_number`, `computed_traits_json` |
| `MealPlanItemPublic` | `computed_traits_json` |

## Migrations

| Revision | Purpose |
| --- | --- |
| `022_computed_traits` | Food groups, public keys, recipe sequences, computed traits backfill |
| `023_ingredient_taxonomy_metadata` | `storage_class`, `culinary_category`, `product_form`, `preservation` |
| `024_ingredient_traits_storage` | `storage_after_opening`, `traits_json` |
| `025_recipe_public_key_length` | Widen `recipes.public_key` for 4+ digit sequence suffixes |

### `022_computed_traits` backfill steps

1. Add nullable columns.
2. Backfill food groups from category mapping.
3. Backfill dish public keys.
4. Backfill recipe sequence numbers and public keys (when dishes exist).
5. Compute recipe traits (when dishes exist; seeds `g`/`ml` if missing).
6. Enforce NOT NULL + unique constraints.

## Scheduler integration

Add `DishCandidate.computed_traits_json` from main recipe traits. Do **not** change weekly target matching in Phase 9.

## Out of scope (Phase 9 initial pass)

- Remove dish tags or tag editor.
- Replace weekly target matching wholesale.
- Trait-based Telegram output.
- Configurable trait thresholds.
- Style inference from ingredients.

## Validation

```bash
cd backend && python3.12 -m pytest
cd frontend && npm test -- --run && npm run build
```

All existing scheduler and weekly-target tests must pass.

## Implementation status

**Completed** on branch `phase-9/computed-recipe-traits` (July 2026).

| Area | Location |
| --- | --- |
| Migration + backfill | `backend/alembic/versions/022_computed_traits.py` |
| Taxonomy metadata | `023_ingredient_taxonomy_metadata.py`, `024_ingredient_traits_storage.py` |
| Recipe key width | `025_recipe_public_key_length.py` |
| Public keys | `backend/mealroulette/services/public_keys.py` |
| Food groups | `backend/mealroulette/services/food_groups.py`, taxonomy YAML under `backend/mealroulette/data/taxonomy/` |
| Recipe traits | `backend/mealroulette/services/recipe_traits.py` |
| Catalog integration | `backend/mealroulette/services/catalog.py` (keys, refresh, resolver) |
| Planning traits | `backend/mealroulette/services/planning.py` |
| Scheduler candidates | `backend/mealroulette/services/scheduler/catalog.py` |
| Resolver | `backend/mealroulette/services/ingredient_resolver.py` |
| Taxonomy APIs | `backend/mealroulette/api/routes/taxonomy.py` |
| Frontend | `frontend/src/features/ingredients/IngredientTaxonomyPage.tsx`, catalog/planning types |
| Tests | `tests/test_computed_traits.py`, `test_recipe_traits.py`, `test_phase9_acceptance.py`, `test_ingredient_resolver.py`, `test_taxonomy_api.py`, `test_taxonomy_loader.py` |

Validation (2026-07-12): `make test-backend` — 189 passed, 2 skipped; frontend — 18 passed, build green. Taxonomy: `make validate-taxonomy` — 412 auto-accepted, 0 blockers.
