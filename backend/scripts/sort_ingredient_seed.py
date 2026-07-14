#!/usr/bin/env python3
"""Sort ingredient seed entries by canonical_name."""

from __future__ import annotations

from pathlib import Path

import yaml

SEED_PATH = Path(__file__).resolve().parents[1] / "mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml"


def main() -> None:
    data = yaml.safe_load(SEED_PATH.read_text(encoding="utf-8"))
    ingredients = data.get("ingredients")
    if not isinstance(ingredients, list):
        raise ValueError("Expected ingredients list in seed file")
    data["ingredients"] = sorted(ingredients, key=lambda entry: entry["canonical_name"])
    SEED_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    print(f"Sorted {len(data['ingredients'])} ingredients in {SEED_PATH}")


if __name__ == "__main__":
    main()
