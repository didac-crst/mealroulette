# Taxonomy proposals (not active truth)

These files are **proposal and validation inputs** from the Phase 9 catalogue expansion pass. They are **not** imported by the running app until reviewed and promoted.

| File | Purpose |
| --- | --- |
| `food_groups.yaml` | Proposed 22 food groups |
| `ingredient_families.yaml` | Proposed 90 ingredient families |
| `candidate_ingredients_flat.yaml` | 627 flat discovery candidates |
| `ingredients_seed_expanded_proposal.yaml` | 627 expanded proposal rows (promotion-shaped) |

**Active truth** remains:

- `backend/mealroulette/data/taxonomy/food_groups.yaml` (22 groups)
- `backend/mealroulette/data/taxonomy/ingredient_families.yaml` (69 families)
- `backend/mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml` (412 ingredients)

## Validate proposals

```bash
cd backend && python3.12 -m mealroulette.commands.validate_taxonomy --proposal
```

Default `validate_taxonomy` validates the **active seed** only. Use `--proposal` for files under this directory.

Optional flags: `--candidates`, `--taxonomy`, `--report`, `--json-report`.

See [docs/taxonomy/taxonomy_validation_workflow_spec.md](../../../docs/taxonomy/taxonomy_validation_workflow_spec.md).
