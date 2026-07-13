# Phase 9 Taxonomy And Ingredient Resolver Spec

## Document metadata

- **Purpose:** Ingredient taxonomy, food groups, families, resolver APIs, and seed structure.
- **Authority:** Canonical feature spec for taxonomy behaviour; ADR 001/002 for durable decisions. Proposal draft: [taxonomy/proposal_taxonomy_and_resolver_spec.md](../taxonomy/proposal_taxonomy_and_resolver_spec.md) (superseded).
- **Status:** Living — update when taxonomy YAML, APIs, or resolver rules change.
- **Update when:** Phase 9+ taxonomy or catalog changes ship.

---

## Purpose

Split ingredient taxonomy into declarative files that can support:

- ingredient seed import
- recipe computed traits
- food group and family browsing APIs
- ingredient resolver APIs for humans and LLM agents
- top-down ingredient selection when direct alias matching fails

This is intended for Phase 9, but must remain compatible with the current v0.5 app.

## Files

Runtime taxonomy files (source of truth):

```text
backend/mealroulette/data/taxonomy/food_groups.yaml
backend/mealroulette/data/taxonomy/ingredient_families.yaml
backend/mealroulette/data/taxonomy/batch_plan.yaml
backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml   # canonical ingredient rows (import target)
```

Loader: `mealroulette.data.taxonomy_loader`.

Handoff reference (may match repo at import time):

```text
/private/tmp/mealroulette_phase9_cursor_handoff.md
/private/tmp/mealroulette_phase9_taxonomy/*
```

Superseded single-file proposal (reference only):

```text
/private/tmp/mealroulette_canonical_ingredients_yaml_proposal.yaml
```

## Design

The taxonomy has three functional levels:

```text
food_group -> ingredient_family -> ingredient
```

Examples:

```text
vegetable -> tomato_family -> cherry_tomato
carbohydrate -> rice_family -> jasmine_rice
meat -> chicken_family -> chicken_breast
fish -> white_fish_family -> hake
seafood -> cephalopod_family -> squid
plant_protein -> soy_family -> firm_tofu
condiment -> soy_sauce_family -> soy_sauce
```

## Vector Semantics

Similarity vectors should be built at the ingredient-family level.

Use:

```text
ingredient -> ingredient_family
```

Do not use individual ingredient keys as the normal vector dimension, and do not collapse similarity vectors all the way to food groups.

Rationale:

- ingredient-level vectors become too sparse as the catalog grows toward 2,000 rows
- food-group vectors are too coarse for meal variety
- family-level vectors preserve useful similarity while keeping the vector vocabulary compact

Examples:

```text
cherry_tomato -> tomato_family
coeur_de_boeuf_tomato -> tomato_family
canned_chopped_tomatoes -> tomato_family

spaghetti -> pasta_family
fideua_noodles -> pasta_family

jasmine_rice -> rice_family
bomba_rice -> rice_family

chicken_breast -> chicken_family
chicken_thigh -> chicken_family
```

Recipe similarity vector:

```json
{
  "tomato_family": 35.0,
  "pasta_family": 45.0,
  "garlic_family": 15.0
}
```

After pantry exclusion and normalization, pantry/background families may disappear.

Layer responsibilities:

| Layer | Primary use |
| --- | --- |
| ingredient | exact recipe content, aliases, shopping, unit conversion |
| ingredient_family | similarity vectors, dominant carb/protein, ingredient navigator grouping |
| food_group | broad filters and traits such as vegan, contains meat, carb-heavy |

Phase 9 rule:

```text
Similarity vector key = ingredient.family
```

Fallback for legacy/incomplete rows only:

```text
if ingredient.family is missing:
    use ingredient.food_group or category as fallback
    count/report this as incomplete taxonomy data
```

Long-term invariant:

```text
Every non-pantry ingredient should have an ingredient_family.
Every ingredient_family should belong to exactly one food_group.
```

## Why Split Files

Food groups, families, and ingredients change at different speeds.

Food groups:

- small controlled vocabulary
- used by computed traits
- should be stable

Ingredient families:

- medium-sized taxonomy
- used for similarity vectors and dominant ingredient traits
- useful for browsing and top-down LLM selection

Ingredients:

- large seed catalog
- contains aliases, descriptions, shopping units, conversions, and review metadata
- can grow toward ~2,000 rows in batches

Batch plan:

- not runtime data
- used to plan curation work and avoid pretending that generated conversion data is authoritative

## Compatibility With Current App

This taxonomy must be additive first.

Do not remove:

```text
tags
dish_tags
Dish.tags
DishPublic.tag_ids
```

Do not replace weekly target matching yet.

Current weekly targets use dish tags. Keep this working:

```text
fish
meat
vegetarian
pasta
rice
soup
```

Computed traits and taxonomy data should be added in parallel. A later explicit migration may map weekly targets to computed traits after tests prove compatibility.

Important: `soup` is not derivable from food groups. It should remain a style/tag target unless a future recipe-style classifier exists.

## Food Group YAML Contract

Each food group:

```yaml
- id: vegetable
  label: Vegetable
  description: >
    ...
```

Requirements:

- `id` is stable, lowercase snake_case
- `label` is human-readable
- `description` should include positive and negative selection guidance
- no duplicate IDs

## Ingredient Family YAML Contract

Each ingredient family:

```yaml
- id: tomato_family
  food_group: vegetable
  label: Tomato family
  description: >
    ...
```

Requirements:

- `id` is stable, lowercase snake_case
- `food_group` must reference a valid food group
- `description` should help an LLM choose this family and avoid nearby wrong families
- no duplicate IDs

## Ingredient YAML Contract

Each ingredient:

```yaml
- canonical_name: cherry_tomato
  display_name: Cherry tomato
  description: >
    Small fresh tomatoes...
  category: vegetable
  food_group: vegetable
  family: tomato_family
  pantry_item: false
  default_recipe_unit: g
  preferred_shopping_unit: g
  aggregation_unit: g
  aggregation_strategy: prefer_mass
  aliases:
    - cherry tomatoes
    - tomate cerise
  unit_conversions:
    - from_unit: unit
      to_unit: g
      factor: 15
      basis: one cherry tomato
      confidence: low
      approved: true
      source: seed_suggestion
```

Requirements:

- `canonical_name` is stable, lowercase snake_case
- `display_name` is human-readable
- `description` is mandatory for LLM-facing resolution
- `food_group` must reference a valid food group
- `family` must reference a valid ingredient family
- ingredient `food_group` should normally equal the family's food group, but exceptions are allowed only when deliberate
- aliases should include common English, French, Spanish, Catalan, and common supermarket names where relevant
- conversions must include confidence/source/approval metadata
- approximate density/count conversions should usually be `approved: false` unless reviewed

## Resolver Strategy

The resolver should support two paths:

```text
Path A: name-first resolution
Path B: top-down classification
```

### Path A: Name-First Resolution

Used when a raw ingredient string likely maps to an existing ingredient.

Build a search index from every known name:

```text
canonical_name
display_name
aliases[]
optional locale names later
optional plural/singular generated variants later
```

Every indexed value points back to one canonical ingredient.

Normalize both query and indexed values:

- lowercase
- trim
- remove accents
- normalize ligatures such as `œ -> oe`
- collapse punctuation and repeated spaces
- compare snake_case and spaced forms
- optionally singularize simple plural forms

Resolver order:

```text
1. exact canonical/display/alias match
2. exact match after stronger normalization
3. token match
4. fuzzy suggestions
5. unknown
```

Recommended fuzzy policy:

```text
if best_score >= 0.95 and gap_to_second >= 0.10:
    auto-resolve
elif best_score >= 0.75:
    return suggestions
else:
    unknown
```

The exact scoring library can be chosen by implementation:

- Python RapidFuzz
- Postgres trigram later
- simple token ratio for first pass

Return matched provenance:

```json
{
  "status": "exact",
  "matched_on": "alias",
  "matched_value": "coeur de boeuf",
  "ingredient": {
    "canonical_name": "coeur_de_boeuf_tomato",
    "display_name": "Coeur de boeuf tomato",
    "family": "tomato_family",
    "food_group": "vegetable"
  }
}
```

Ambiguous result:

```json
{
  "status": "suggestions",
  "query": "cream",
  "suggestions": [
    {
      "canonical_name": "heavy_cream",
      "display_name": "Heavy cream",
      "family": "dairy_family",
      "food_group": "dairy",
      "score": 0.91
    },
    {
      "canonical_name": "creme_fraiche",
      "display_name": "Creme fraiche",
      "family": "dairy_family",
      "food_group": "dairy",
      "score": 0.87
    }
  ]
}
```

Do not auto-map ambiguous generic words like:

```text
cream
cheese
pepper
rice
noodles
curry
sauce
fish
beans
```

unless context and score make it unambiguous.

### Path B: Top-Down Classification

Used when name-first resolution is unknown or ambiguous.

Flow:

```text
food_group -> ingredient_family -> ingredient
```

Example:

```text
"poivron del piquillo"
-> food_group: vegetable
-> family: pepper_family
-> ingredient: piquillo_pepper
```

Descriptions are critical here. Each description should include:

- what belongs in this group/family/ingredient
- what does not belong
- important near-miss alternatives

Top-down API options:

```text
GET /api/food-groups
GET /api/food-groups/{id}/families
GET /api/ingredient-families/{id}/ingredients
POST /api/ingredients/classify-candidate
```

Suggested classify request:

```json
{
  "name": "poivron del piquillo",
  "context": "Spanish roasted peppers in a jar used for stuffing",
  "language": "mixed"
}
```

Suggested classify response:

```json
{
  "status": "guided_suggestions",
  "food_groups": [
    {
      "id": "vegetable",
      "reason": "Peppers are vegetables and not a dry spice in this context."
    }
  ],
  "families": [
    {
      "id": "pepper_family",
      "food_group": "vegetable",
      "reason": "Piquillo is a preserved red pepper."
    }
  ],
  "ingredients": [
    {
      "canonical_name": "piquillo_pepper",
      "family": "pepper_family",
      "food_group": "vegetable",
      "reason": "Best match for Spanish piquillo peppers."
    }
  ]
}
```

## Human Ingredient Navigator

The same taxonomy should power a human-facing ingredient navigator in the admin/catalog UI.

Purpose:

- help humans inspect and curate the canonical ingredient taxonomy
- make food groups, families, ingredients, aliases, and conversions understandable
- support manual correction when LLM or alias resolution is ambiguous
- make Phase 9 computed traits auditable

Recommended route:

```text
/ingredients/taxonomy
```

or as a tab/section under the existing ingredient admin area:

```text
/ingredients
  - List
  - Taxonomy
  - Resolver
```

Navigator hierarchy:

```text
Food groups
  -> Families inside selected food group
    -> Ingredients inside selected family
      -> aliases, descriptions, units, conversions, pantry flag
```

Recommended UI capabilities:

- show overview counts:
  - total food groups
  - total ingredient families
  - total ingredients
  - total aliases
  - total approved conversions
  - total unapproved/suggested conversions
- for each food group, show:
  - number of child families
  - number of ingredients across those families
  - number of ingredients missing required metadata
- for each ingredient family, show:
  - number of child ingredients
  - number of aliases across child ingredients
  - number of approved and unapproved conversions
- search by canonical name, display name, or alias
- browse by food group
- browse by ingredient family
- show food group description and family description side by side
- show all aliases for an ingredient
- show unit conversions with confidence, source, and approval status
- highlight ingredients missing family or food group
- highlight duplicate or ambiguous aliases
- show whether the ingredient contributes to similarity vectors
- show whether the ingredient is excluded as pantry
- show computed impact examples:
  - family vector key: `tomato_family`
  - food group: `vegetable`
  - pantry excluded: yes/no

Overview examples:

```json
{
  "totals": {
    "food_groups": 20,
    "families": 58,
    "ingredients": 2034,
    "aliases": 8450,
    "approved_conversions": 610,
    "unapproved_conversions": 420
  },
  "food_groups": [
    {
      "id": "vegetable",
      "family_count": 14,
      "ingredient_count": 360,
      "missing_metadata_count": 3
    },
    {
      "id": "carbohydrate",
      "family_count": 8,
      "ingredient_count": 240,
      "missing_metadata_count": 0
    }
  ]
}
```

Suggested API:

```text
GET /api/ingredient-taxonomy/overview
```

The overview endpoint should be cheap to call from the navigator landing page and should not require loading every ingredient row.

Resolver UI:

```text
input raw ingredient text -> show exact/suggestions/unknown
```

For unknown inputs, offer the same top-down selection used by LLM agents:

```text
choose food group -> choose family -> choose existing ingredient or draft new ingredient
```

Draft-new-ingredient form should prefill:

- canonical name
- display name
- aliases
- food group
- family
- description
- default recipe unit
- preferred shopping unit
- pantry flag
- suggested conversions marked unapproved

This UI should not be required to complete all Phase 9 backend work, but the backend/API should be designed so the navigator is straightforward to build.

## LLM Agent Workflow

Recommended resolver order for agents:

```yaml
selection_guidance:
  resolver_order:
    - exact_canonical_or_alias
    - normalized_alias
    - fuzzy_suggestions
    - top_down_food_group_family_ingredient
    - draft_new_ingredient_for_review
```

If the ingredient does not exist after top-down selection, create a draft proposal, not a committed catalog row:

```yaml
canonical_name: proposed_name
display_name: Proposed Name
description: ...
food_group: ...
family: ...
aliases: [...]
unit_conversions: []
review_status: needs_human_review
```

## Asian Ingredients Scope

Include Asian ingredients commonly available in Europe and used in European home cooking.

Examples:

- soy sauce, tamari
- fish sauce, oyster sauce, hoisin, sriracha, gochujang
- miso
- tofu, tempeh, edamame
- rice noodles, ramen, udon, soba, glass noodles
- rice paper and dumpling wrappers
- Thai curry pastes
- coconut milk and coconut cream
- ginger, galangal, lemongrass
- shiitake and other Asian mushrooms
- nori, wakame
- sesame seeds and toasted sesame oil

Descriptions and aliases are especially important in this area because LLMs often confuse:

- soy sauce vs tamari
- fish sauce vs oyster sauce
- curry paste vs curry powder
- coconut milk vs coconut cream
- ramen vs rice noodles
- tofu vs tempeh
- ginger vs galangal

## Ingestion Order

Load in this order:

```text
food_groups.yaml
ingredient_families.yaml
mealroulette_ingredients_seed.yaml   # under data/fixtures/
```

Validate before writing to DB:

- every family references an existing food group
- every ingredient references existing food group and family
- no duplicate food group IDs
- no duplicate family IDs
- no duplicate canonical names
- no duplicate aliases unless explicitly allowed and disambiguated
- unit symbols exist
- conversion factors are positive
- conversion confidence/source values are valid

## Batch Growth Strategy

Do not generate 2,000 final ingredients in one unreviewed pass.

Grow the taxonomy by reviewed batches:

- vegetables and fruits
- seafood and fish
- meat and charcuterie
- grains, pasta, bread
- cheeses and dairy
- legumes, nuts, seeds
- oils, condiments, sauces
- spices and herbs
- stocks, alcohol, preserves
- regional French/Spanish specialties
- Europe-common Asian staples
- alias cleanup and ambiguity review

## Phase 9 Implementation Advice

Suggested commit order:

1. Add taxonomy split spec and YAML files.
2. Add loaders and validation for food groups/families/ingredients.
3. Add `food_group` to ingredients and import it.
4. Add resolver index and exact/alias resolution.
5. Add top-down browsing APIs.
6. Add fuzzy suggestions, with conservative auto-match thresholds.
7. Add draft-new-ingredient response path.

Do not block the main computed-traits work on a full 2,000-row catalog. The schema, loader, resolver, and representative seed are enough for Phase 9.

## Implementation status

**Completed** on branch `phase-9/computed-recipe-traits` (July 2026).

| Component | Location |
| --- | --- |
| Taxonomy YAML | `backend/mealroulette/data/taxonomy/` (`food_groups.yaml`, `ingredient_families.yaml`, `batch_plan.yaml`) |
| Ingredient seed | `backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml` — single canonical import file; validated against taxonomy on every import |
| Loader + validation | `backend/mealroulette/data/taxonomy_loader.py` |
| Name normalization | `backend/mealroulette/services/names.py` |
| Resolver service | `backend/mealroulette/services/ingredient_resolver.py` |
| Taxonomy service | `backend/mealroulette/services/taxonomy_service.py` |
| API routes | `GET /api/food-groups`, `GET /api/food-groups/{id}/families`, `GET /api/ingredient-families/{id}/ingredients`, `GET /api/ingredient-taxonomy/overview`, `POST /api/ingredients/resolve-v2`, `POST /api/ingredients/classify-candidate`; legacy `POST /api/ingredients/resolve` upgraded |
| Frontend navigator | `/ingredients/taxonomy` — browse groups/families/ingredients + resolver panel |
| Tests | `tests/test_ingredient_resolver.py`, `tests/test_taxonomy_api.py`, `tests/test_taxonomy_loader.py` |

Removed: `taxonomy/ingredients_seed.yaml` (superseded by the fixtures seed above). The embedded `ingredient_families` block in the fixtures file is also removed — families live only in `ingredient_families.yaml`.

Full ~2,000-row catalog growth via `batch_plan.yaml` remains a **later explicit step**. The revised MVP target is **500–700** reviewed ingredients — see [docs/taxonomy/catalogue_assessment_and_mvp_plan.md](../taxonomy/catalogue_assessment_and_mvp_plan.md).

## Catalogue status (July 2026)

**Expansion frozen** per [ADR 001](../adr/001-ingredient-taxonomy-contract.md). Active catalogue reconciled from proposal:

- **412 ingredients** in `mealroulette_ingredients_seed.yaml`
- **69 families**, **22 food groups**
- Validator: **0 blockers**, **0 needs_human_review** (`make validate-taxonomy`)

Reconcile command: `make reconcile-taxonomy`

Proposal rows remain in `proposals/` for reference; only promoted rows are in the active seed.

Expanded proposals live under `backend/mealroulette/data/taxonomy/proposals/` (627 candidates, 90 families, 22 food groups). **Do not import until promoted.**

Deterministic validation:

```bash
cd backend && python3.12 -m mealroulette.commands.validate_taxonomy
```

Reports: [docs/taxonomy/reports/taxonomy_validation_report.md](../taxonomy/reports/taxonomy_validation_report.md).

Workflow spec: [docs/taxonomy/taxonomy_validation_workflow_spec.md](../taxonomy/taxonomy_validation_workflow_spec.md).

Index: [docs/taxonomy/README.md](../taxonomy/README.md).
