"""Apply unit conversion approval policy to the active ingredient seed."""

from __future__ import annotations

from mealroulette.data.conversion_policy import apply_conversion_policy_to_seed
from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH


def main() -> None:
    count = apply_conversion_policy_to_seed(DEFAULT_INGREDIENT_SEED_PATH)
    print(f"Applied conversion policy to {count} ingredient(s) in {DEFAULT_INGREDIENT_SEED_PATH}")


if __name__ == "__main__":
    main()
