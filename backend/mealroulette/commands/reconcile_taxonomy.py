"""Reconcile active ingredient seed with validated proposal subset (ADR 001)."""

from __future__ import annotations

import sys

from mealroulette.data.taxonomy_reconcile import write_reconciled_catalogue


def main() -> None:
    result = write_reconciled_catalogue()
    print(
        f"Reconciled catalogue: {result.ingredient_count} ingredients, "
        f"{result.families_count} families "
        f"(renamed {result.renamed_active} active, merged {result.merged_from_proposal}, "
        f"skipped {result.skipped_proposal} proposal rows)."
    )
    print("Updated active seed and taxonomy YAML. Run `make validate-taxonomy` against active paths next.")


if __name__ == "__main__":
    main()
