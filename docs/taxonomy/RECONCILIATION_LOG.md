# Taxonomy Reconciliation Log

## Document metadata

- **Purpose:** Record of taxonomy reconciliation from proposal to active seed (July 2026).
- **Authority:** Historical log — current seed is runtime truth under `backend/mealroulette/data/`.
- **Status:** Frozen log.
- **Update when:** Do not update except to fix broken links.

---

**Date:** 2026-07-12  
**ADR:** [001-ingredient-taxonomy-contract.md](../adr/001-ingredient-taxonomy-contract.md)

## Outcome

| Metric | Before | After |
| --- | ---: | ---: |
| Active ingredients | 108 | **412** |
| Families | 55 | **69** |
| Food groups | 20 | **22** |
| Validation blockers | 5 | **0** |

## Actions applied

1. **Policy ADR** — granularity, aliases, food_group vs culinary_category, storage_class.
2. **Schema** — migration `023`: `storage_class`, `culinary_category`, `product_form`, `preservation`.
3. **Reconciliation** — merged active seed + safe proposal subset; skipped 242 `needs_human_review` proposal rows.
4. **Blockers resolved** — alias ownership rules, merges (fish_fumet→fish_stock, whipping→heavy_cream, etc.).
5. **Granularity** — generic canonicals (hake, salmon, thyme, sage, onion); forms as aliases/metadata.
6. **Renames** — `hake_fillet`→`hake`, `salmon_fillet`→`salmon`, `eggs`→`egg`, `calamari`→`squid` (old IDs as aliases).
7. **Empty families populated** — celery, fennel_bulb, tropical fruits assigned.

## Commands

```bash
make reconcile-taxonomy        # merge proposal → active YAML
make apply-conversion-policy   # normalize conversion approval classes
make validate-taxonomy         # exception report
```

## Conversion policy (2026-07-12)

Applied three-class policy to **33** flagged ingredients (`conversion_policy.py`). Validator: **0 suspicious conversions**.

| Class | Count | Rule |
| --- | ---: | --- |
| 1 — size estimates | 20 | `unit`/`fillet`/`bunch`→`g`: `approximate`, `approved: false` |
| 2 — herbs/citrus/aromatics | 10 | Same; no `tsp`/`bunch`→`g` approval |
| 3 — sheets/drained | 3 | `product_form: sheet` for pastry; capers `tbsp→ml` exact approved |

Only deterministic pairs approved: `tbsp→ml`, `tsp→ml`, `kg→g`, `l→ml`.

## Human review batch (2026-07-12)

Resolved **17** active ingredients previously tagged `needs_human_review`:

| Decision | Ingredients |
| --- | --- |
| `squash_family` for pumpkin (butternut aliases stay on pumpkin row) | pumpkin |
| `corn_family` + `traits.starchy: true`; vegetable not carbohydrate | sweetcorn |
| `nut_seed` + `culinary_category: condiment` | peanut_butter |
| `hard_cheese_family` + `product_form: grated` | grated_cheese |
| `approved_exception` for tomato paste condiment rule | tomato_paste |
| Storage / family confirmations | avocado, canned_chopped_tomatoes, black_olives, capers, coconut_milk, mayonnaise (+ `storage_after_opening`), curry_powder, oregano, cream_cheese, fish_stock, vegetable_stock, white_wine |

Added **`corn_family`** (69 families). Migrations **`024`** (`storage_after_opening`, `traits_json`) and **`025`** (recipe public key width).

```bash
cd backend && python -m mealroulette.data.apply_human_review_decisions
make validate-taxonomy
```

## Deferred (intentional)

- ~215 proposal rows remain un-promoted (`needs_human_review`).
- LLM semantic validation batch.
- Recipe-driven growth (Iteration 4 in assessment plan).
