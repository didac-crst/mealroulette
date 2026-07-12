"""Apply owner-approved taxonomy decisions for the 17 human-review ingredients."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mealroulette.data.taxonomy_loader import validate_ingredient_taxonomy_rows

SEED_PATH = Path(__file__).resolve().parent / "fixtures" / "mealroulette_ingredients_seed.yaml"

# Owner-approved 2026-07-12 — see docs/taxonomy/RECONCILIATION_LOG.md
REVIEW_DECISIONS: dict[str, dict[str, Any]] = {
    "avocado": {
        "food_group": "fruit",
        "family": "tropical_fruit_family",
        "storage_class": "fresh_produce",
        "review_status": "candidate",
    },
    "pumpkin": {
        "food_group": "vegetable",
        "family": "squash_family",
        "storage_class": "fresh_produce",
        "review_status": "candidate",
    },
    "sweetcorn": {
        "category": "vegetable",
        "food_group": "vegetable",
        "family": "corn_family",
        "storage_class": "fresh_produce",
        "traits": {"starchy": True},
        "review_status": "candidate",
    },
    "canned_chopped_tomatoes": {
        "food_group": "vegetable",
        "family": "tomato_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "tomato_paste": {
        "food_group": "condiment",
        "culinary_category": "condiment",
        "family": "tomato_family",
        "storage_class": "ambient",
        "review_status": "approved_exception",
        "review_note": "Tomato-derived product treated as a condiment for meal composition.",
    },
    "peanut_butter": {
        "food_group": "nut_seed",
        "culinary_category": "condiment",
        "family": "nut_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "black_olives": {
        "food_group": "condiment",
        "family": "olive_pickle_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "capers": {
        "food_group": "condiment",
        "family": "olive_pickle_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "coconut_milk": {
        "food_group": "condiment",
        "family": "coconut_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "mayonnaise": {
        "food_group": "condiment",
        "family": "prepared_sauce_family",
        "storage_class": "ambient",
        "storage_after_opening": "refrigerated",
        "review_status": "candidate",
    },
    "curry_powder": {
        "food_group": "spice",
        "family": "spice_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "oregano": {
        "food_group": "herb",
        "family": "herb_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "cream_cheese": {
        "food_group": "cheese",
        "family": "fresh_cheese_family",
        "storage_class": "refrigerated",
        "review_status": "candidate",
    },
    "grated_cheese": {
        "food_group": "cheese",
        "family": "hard_cheese_family",
        "product_form": "grated",
        "storage_class": "refrigerated",
        "review_status": "candidate",
    },
    "fish_stock": {
        "food_group": "stock",
        "family": "stock_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "vegetable_stock": {
        "food_group": "stock",
        "family": "stock_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
    "white_wine": {
        "food_group": "alcohol",
        "family": "wine_family",
        "storage_class": "ambient",
        "review_status": "candidate",
    },
}


def _apply_patch(row: dict[str, Any], patch: dict[str, Any]) -> None:
    for key, value in patch.items():
        if key == "traits" and isinstance(value, dict):
            existing = row.get("traits")
            if isinstance(existing, dict):
                row["traits"] = {**existing, **value}
            else:
                row["traits"] = dict(value)
        else:
            row[key] = value


def apply_review_decisions(rows: list[dict[str, Any]]) -> list[str]:
    """Return canonical names that were patched."""
    by_name = {row["canonical_name"]: row for row in rows}
    missing = [name for name in REVIEW_DECISIONS if name not in by_name]
    if missing:
        raise KeyError(f"Seed missing review ingredients: {missing}")

    patched: list[str] = []
    for name, patch in REVIEW_DECISIONS.items():
        _apply_patch(by_name[name], patch)
        patched.append(name)
    return patched


def main() -> None:
    with SEED_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    rows = data["ingredients"]
    patched = apply_review_decisions(rows)
    errors = validate_ingredient_taxonomy_rows(rows)
    if errors:
        raise SystemExit(f"Taxonomy validation failed after review patch: {errors[:5]}")

    with SEED_PATH.open("w", encoding="utf-8") as handle:
        yaml.dump(
            data,
            handle,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=120,
        )

    print(f"Applied review decisions to {len(patched)} ingredients: {', '.join(patched)}")


if __name__ == "__main__":
    main()
