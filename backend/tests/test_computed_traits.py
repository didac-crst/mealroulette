from mealroulette.services.food_groups import food_group_for_ingredient
from mealroulette.services.public_keys import (
    DISH_PUBLIC_KEY_LENGTH,
    generate_dish_public_key,
    generate_recipe_public_key,
    slug_from_dish_name,
    validate_dish_public_key,
    validate_recipe_public_key,
)


def test_slug_from_dish_name_truncates_and_normalizes():
    slug = slug_from_dish_name("Chicken & Rice Bowl!")
    assert slug
    assert len(slug) <= 20
    assert all(char in "0123456789abcdefghjkmnpqrstvwxyz" for char in slug)


def test_generate_dish_public_key_length_and_format():
    public_key = generate_dish_public_key("Mushroom Risotto")
    assert len(public_key) == DISH_PUBLIC_KEY_LENGTH
    assert validate_dish_public_key(public_key)


def test_generate_dish_public_key_is_stable_for_same_name_attempt():
    first = generate_dish_public_key("Test Dish")
    second = generate_dish_public_key("Test Dish")
    assert first.split("-", 1)[0] == second.split("-", 1)[0]


def test_generate_recipe_public_key():
    dish_key = generate_dish_public_key("Pasta")
    recipe_key = generate_recipe_public_key(dish_key, 1)
    assert validate_recipe_public_key(recipe_key, dish_public_key=dish_key)
    assert recipe_key.endswith("-001")


def test_food_group_mapping_and_override():
    assert food_group_for_ingredient(food_group=None, category="pasta") == "carbohydrate"
    assert food_group_for_ingredient(food_group=None, category="unknown") == "other"
    assert food_group_for_ingredient(food_group="meat", category="vegetable") == "meat"
