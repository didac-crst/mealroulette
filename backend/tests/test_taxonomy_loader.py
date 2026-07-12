from mealroulette.data.taxonomy_loader import (
    family_to_food_group,
    food_group_ids,
    load_food_groups,
    load_ingredient_families,
    validate_ingredient_taxonomy_rows,
)


def test_food_groups_load_from_yaml():
    groups = load_food_groups()
    assert len(groups) == 22
    assert groups[0].id == "vegetable"
    assert "vegetable" in food_group_ids()


def test_ingredient_families_reference_valid_food_groups():
    families = load_ingredient_families()
    assert len(families) >= 40
    mapping = family_to_food_group()
    assert mapping["tomato_family"] == "vegetable"
    assert mapping["pasta_family"] == "carbohydrate"
    assert all(family.food_group in food_group_ids() for family in families)


def test_validate_ingredient_seed_passes():
    from pathlib import Path

    import yaml

    path = Path(__file__).resolve().parents[1] / "mealroulette/data/fixtures/mealroulette_ingredients_seed.yaml"
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    errors = validate_ingredient_taxonomy_rows(data["ingredients"])
    assert errors == []
