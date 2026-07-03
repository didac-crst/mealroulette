import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mealroulette.core.config import settings
from mealroulette.data.seed_catalog import seed_catalog_data


def seed_reference_data() -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with Session(engine) as db:
        result = seed_catalog_data(db)

    if result.total_added == 0:
        print("Reference catalog data already up to date.")
        return

    print(
        f"Added {result.units_added} unit(s), {result.tags_added} tag(s), "
        f"and {result.conversions_added} ingredient conversion(s)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load reference units and tags from YAML if they are not already in the database."
    )
    parser.parse_args()
    seed_reference_data()


if __name__ == "__main__":
    main()
