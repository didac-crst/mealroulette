import pytest
from sqlalchemy import select

from mealroulette.data.import_ingredients import DEFAULT_INGREDIENT_SEED_PATH, import_ingredient_seed
from mealroulette.data.seed_catalog import seed_catalog_data
from mealroulette.data.seed_taxonomy import (
    backfill_ingredient_family_ids,
    count_ingredients_missing_family_id,
    seed_taxonomy_data,
)
from mealroulette.models.catalog import Ingredient

pytestmark = pytest.mark.integration


def _ingredient(db_session, canonical_name: str) -> Ingredient:
    row = db_session.scalar(select(Ingredient).where(Ingredient.canonical_name == canonical_name))
    assert row is not None
    return row


def test_backfill_maps_legacy_families_from_seed_and_aliases(db_session):
    seed_catalog_data(db_session)
    import_ingredient_seed(db_session, DEFAULT_INGREDIENT_SEED_PATH)
    seed_taxonomy_data(db_session)
    legacy_cases = {
        "green_beans": ("bean_vegetable_family", "green_bean_family"),
        "red_cabbage": ("cabbage_family", "brassica_family"),
        "grated_cheese": ("cheese_family", "hard_cheese_family"),
        "cream_cheese": ("cheese_family", "fresh_cheese_family"),
        "firm_tofu": ("tofu_soy_family", "soy_family"),
        "black_olives": ("olive_family", "olive_pickle_family"),
    }
    for canonical_name, (legacy_family, expected_family) in legacy_cases.items():
        ingredient = _ingredient(db_session, canonical_name)
        ingredient.family = legacy_family
        ingredient.family_id = None
    db_session.flush()

    hake_fillet = Ingredient(
        canonical_name="hake fillet",
        display_name="Hake fillet",
        family="seafood_family",
        family_id=None,
        pantry_item=False,
    )
    db_session.add(hake_fillet)
    db_session.flush()

    backfilled = backfill_ingredient_family_ids(db_session)
    assert backfilled >= len(legacy_cases) + 1

    for canonical_name, (_legacy_family, expected_family) in legacy_cases.items():
        ingredient = _ingredient(db_session, canonical_name)
        assert ingredient.family == expected_family
        assert ingredient.family_id == expected_family

    hake_fillet = _ingredient(db_session, "hake fillet")
    assert hake_fillet.family_id == "white_fish_family"
    assert count_ingredients_missing_family_id(db_session) == 0
