import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mealroulette.core.config import settings
from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH, import_ingredient_seed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import canonical ingredients from a YAML seed into the catalog."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_INGREDIENT_SEED_PATH,
        help=f"Path to ingredient seed YAML (default: {DEFAULT_INGREDIENT_SEED_PATH.name})",
    )
    parser.add_argument(
        "--no-bootstrap-approve",
        action="store_true",
        help="Do not auto-approve approximate conversions for allow_approximate_conversion ingredients",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Ingredient seed file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as db:
        try:
            result = import_ingredient_seed(
                db,
                args.file,
                bootstrap_approve=not args.no_bootstrap_approve,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)

    print(
        "Imported "
        f"{result.ingredients_added} ingredient(s), "
        f"{result.aliases_added} alias(es), "
        f"{result.conversions_added} conversion(s), "
        f"{result.units_added} unit(s)."
    )
    if result.ingredients_updated:
        print(f"Updated {result.ingredients_updated} existing ingredient(s) from seed metadata.")
    if result.ingredients_skipped:
        print(f"Skipped {result.ingredients_skipped} existing ingredient(s); added missing aliases/conversions.")
    if result.unknown_unit_skips:
        print(f"Skipped {result.unknown_unit_skips} conversion(s) with unknown unit symbols.")


if __name__ == "__main__":
    main()
