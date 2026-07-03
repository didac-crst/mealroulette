import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mealroulette.core.config import settings
from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures


def import_sample_dishes(fixture_path: Path) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with Session(engine) as db:
        result = import_dish_fixtures(db, fixture_path)

    if result.total_added == 0 and result.dishes_skipped:
        print(f"All {result.dishes_skipped} dish(es) already present; nothing to import.")
        return

    print(
        "Imported "
        f"{result.dishes_added} dish(es), "
        f"{result.recipes_added} recipe(s), "
        f"{result.steps_added} step(s), "
        f"{result.ingredients_added} recipe ingredient line(s) "
        f"({result.ingredients_created} new ingredient(s))."
    )
    if result.dishes_skipped:
        print(f"Skipped {result.dishes_skipped} existing dish(es) by name.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import sample dishes from a YAML fixture into the catalog."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help=f"Path to fixture YAML (default: {DEFAULT_FIXTURE_PATH.name})",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Fixture file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        import_sample_dishes(args.file)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
