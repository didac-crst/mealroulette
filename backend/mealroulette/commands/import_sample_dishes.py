import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mealroulette.core.config import settings
from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATHS, import_dish_fixtures


def import_sample_dishes(fixture_paths: list[Path]) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    total_dishes_added = 0
    total_dishes_skipped = 0
    total_recipes_added = 0
    total_steps_added = 0
    total_ingredients_added = 0
    total_ingredients_created = 0
    with Session(engine) as db:
        for fixture_path in fixture_paths:
            result = import_dish_fixtures(db, fixture_path)
            total_dishes_added += result.dishes_added
            total_dishes_skipped += result.dishes_skipped
            total_recipes_added += result.recipes_added
            total_steps_added += result.steps_added
            total_ingredients_added += result.ingredients_added
            total_ingredients_created += result.ingredients_created

    if total_dishes_added == 0 and total_dishes_skipped:
        print(f"All {total_dishes_skipped} dish(es) already present; nothing to import.")
        return

    print(
        "Imported "
        f"{total_dishes_added} dish(es), "
        f"{total_recipes_added} recipe(s), "
        f"{total_steps_added} step(s), "
        f"{total_ingredients_added} recipe ingredient line(s) "
        f"({total_ingredients_created} new ingredient(s))."
    )
    if total_dishes_skipped:
        print(f"Skipped {total_dishes_skipped} existing dish(es) by name.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import sample dishes from a YAML fixture into the catalog."
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        help="Path to fixture YAML. May be repeated. Defaults to the bundled sample and simple dish fixtures.",
    )
    args = parser.parse_args()
    fixture_paths = args.file or list(DEFAULT_FIXTURE_PATHS)

    for fixture_path in fixture_paths:
        if not fixture_path.is_file():
            print(f"Fixture file not found: {fixture_path}", file=sys.stderr)
            sys.exit(1)

    try:
        import_sample_dishes(fixture_paths)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
