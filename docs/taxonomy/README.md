# Taxonomy documentation

Phase 9 ingredient taxonomy specs, proposals, and validation reports.

## Active truth (runtime)

| File | Role |
| --- | --- |
| [backend/mealroulette/data/taxonomy/food_groups.yaml](../backend/mealroulette/data/taxonomy/food_groups.yaml) | 22 food groups |
| [backend/mealroulette/data/taxonomy/ingredient_families.yaml](../backend/mealroulette/data/taxonomy/ingredient_families.yaml) | 69 families |
| [backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml](../backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml) | 412 canonical ingredients (import target) |

See also [TAXONOMY_AND_RESOLVER.md](../TAXONOMY_AND_RESOLVER.md) and [COMPUTED_TRAITS.md](../COMPUTED_TRAITS.md).

## Proposals (not active)

Expanded MVP catalogue proposal (~627 candidates, 90 families, 22 food groups):

- [backend/mealroulette/data/taxonomy/proposals/](../backend/mealroulette/data/taxonomy/proposals/)
- [catalogue_assessment_and_mvp_plan.md](catalogue_assessment_and_mvp_plan.md) — target **500–700** ingredients for MVP, not 2,000 immediately
- [proposal_taxonomy_and_resolver_spec.md](proposal_taxonomy_and_resolver_spec.md) — updated resolver/taxonomy spec from handoff

**Do not import proposals until validated and promoted.**

## Validation workflow

- [taxonomy_validation_workflow_spec.md](taxonomy_validation_workflow_spec.md) — deterministic + LLM + human exception review
- [llm_taxonomy_review_prompt.md](llm_taxonomy_review_prompt.md) — LLM batch review prompt (future step)

Run the deterministic validator:

```bash
cd backend && python3.12 -m mealroulette.commands.validate_taxonomy
```

Latest exception report (regenerate with `make validate-taxonomy` after seed or taxonomy changes):

- [reports/taxonomy_validation_report.md](reports/taxonomy_validation_report.md)
- [reports/taxonomy_validation_report.json](reports/taxonomy_validation_report.json)

**Commit policy:** these reports are **checked in** as the last-known-good validation snapshot for the active seed. They are not hand-edited — run `make validate-taxonomy` whenever `mealroulette_ingredients_seed.yaml` or files under `backend/mealroulette/data/taxonomy/` change, then commit the updated reports alongside the data change.

## MVP policy highlights (from assessment)

- **Families** are the similarity-vector level; food groups drive computed traits.
- **`food_group`** describes what the ingredient is; **`pantry_item` / `storage_class`** describe storage/shopping behaviour.
- Flag `food_group: pantry` when a semantic group exists (e.g. canned tomatoes → `food_group: vegetable`, `storage_class: pantry`).
- Promote candidates in reviewed batches; human reviews **exceptions only**, not all rows.
