import pytest
from sqlalchemy import select

from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, Unit
from mealroulette.models.enums import DishCourse, DishStatus, RecipeType
from mealroulette.services.public_keys import (
    PUBLIC_KEY_ALPHABET,
    generate_dish_public_key,
    generate_recipe_public_key,
    slug_from_dish_name,
    validate_dish_public_key,
)
from mealroulette.services.recipe_traits import compute_recipe_traits_now
from mealroulette.services.scheduler.catalog import load_dish_candidates
from mealroulette.data.default_planning_rules import DEFAULT_PLANNING_RULES_JSON
from mealroulette.models.scheduler import PlanningRule, SchedulerSettings, DEFAULT_PLANNING_RULE_ID, SCHEDULER_SETTINGS_ID
from mealroulette.schemas.scheduler import PlanningRulesConfig


def _add_ingredient_line(db_session, recipe, *, canonical_name, food_group, quantity):
    unit = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    ingredient = Ingredient(
        canonical_name=canonical_name,
        display_name=canonical_name,
        category=food_group,
        food_group=food_group,
        family=f"{canonical_name}_family",
    )
    db_session.add(ingredient)
    db_session.flush()
    db_session.add(
        RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=quantity,
            unit_id=unit.id,
        )
    )


@pytest.mark.integration
def test_recipe_get_recomputes_traits_on_the_fly(client, catalog_seed, admin_headers, db_session):
    dish_resp = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Fresh Traits Dish", "status": "active", "tag_ids": []},
    )
    dish_id = dish_resp.json()["id"]
    recipe = client.post(
        f"/api/dishes/{dish_id}/recipes",
        headers=admin_headers,
        json={"variant_name": "main", "is_main": True},
    ).json()
    gram = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    spaghetti = Ingredient(
        canonical_name="fresh_traits_spaghetti",
        display_name="Spaghetti",
        category="pasta",
        food_group="carbohydrate",
        family="pasta_family",
    )
    db_session.add(spaghetti)
    db_session.flush()
    client.post(
        f"/api/recipes/{recipe['id']}/ingredients",
        headers=admin_headers,
        json={"ingredient_id": spaghetti.id, "quantity": "500", "unit_id": gram.id},
    )

    stored = db_session.get(Recipe, recipe["id"])
    stored.computed_traits_json = {
        "food_group_weights": {"fruit": 100.0},
        "contains_food_groups": ["fruit"],
        "vegan": True,
        "contains_meat": False,
        "carb_heavy": False,
        "dominant_carb": None,
        "dominant_protein": None,
        "family_vector": {},
    }
    db_session.commit()

    payload = client.get(f"/api/recipes/{recipe['id']}", headers=admin_headers).json()
    weights = payload["computed_traits_json"]["food_group_weights"]
    assert weights.get("carbohydrate", 0) > weights.get("fruit", 0)
    assert "carbohydrate" in payload["computed_traits_json"]["contains_food_groups"]


@pytest.mark.integration
def test_dish_get_uses_fresh_main_recipe_traits(client, catalog_seed, admin_headers, db_session):
    dish_resp = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Fresh Dish Traits", "status": "active", "tag_ids": []},
    )
    dish_id = dish_resp.json()["id"]
    recipe = client.post(
        f"/api/dishes/{dish_id}/recipes",
        headers=admin_headers,
        json={"variant_name": "main", "is_main": True},
    ).json()
    gram = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    carb = Ingredient(
        canonical_name="fresh_dish_carb",
        display_name="Carb",
        category="grain",
        food_group="carbohydrate",
        family="rice_family",
    )
    db_session.add(carb)
    db_session.flush()
    client.post(
        f"/api/recipes/{recipe['id']}/ingredients",
        headers=admin_headers,
        json={"ingredient_id": carb.id, "quantity": "400", "unit_id": gram.id},
    )

    stored = db_session.get(Recipe, recipe["id"])
    stored.computed_traits_json = {"food_group_weights": {"fruit": 100.0}, "contains_food_groups": ["fruit"]}
    db_session.commit()

    payload = client.get(f"/api/dishes/{dish_id}", headers=admin_headers).json()
    assert payload["computed_traits_json"]["food_group_weights"].get("carbohydrate", 0) >= 90


@pytest.mark.integration
def test_recipe_public_key_lookup(client, catalog_seed, admin_headers):
    dish_id = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Public Key Lookup Dish", "status": "active", "tag_ids": []},
    ).json()["id"]
    recipe = client.post(
        f"/api/dishes/{dish_id}/recipes",
        headers=admin_headers,
        json={"variant_name": "main", "is_main": True},
    ).json()

    by_id = client.get(f"/api/recipes/{recipe['id']}", headers=admin_headers)
    by_key = client.get(f"/api/recipes/by-key/{recipe['public_key']}", headers=admin_headers)
    assert by_id.status_code == 200
    assert by_key.status_code == 200
    assert by_key.json()["id"] == recipe["id"]
    assert by_key.json()["public_key"] == recipe["public_key"]

    missing = client.get("/api/recipes/by-key/does-not-exist-001", headers=admin_headers)
    assert missing.status_code == 404


@pytest.mark.integration
def test_scheduler_uses_fresh_traits(db_session, catalog_seed, scheduler_seed):
    dish = Dish(
        public_key=generate_dish_public_key("Scheduler Fresh Traits"),
        name="Scheduler Fresh Traits",
        course=DishCourse.main,
        status=DishStatus.active,
    )
    db_session.add(dish)
    db_session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        public_key=generate_recipe_public_key(dish.public_key, 1),
        sequence_number=1,
        variant_name="main",
        recipe_type=RecipeType.standard,
        is_main=True,
        computed_traits_json={"contains_food_groups": ["fish"], "contains_meat": False},
    )
    db_session.add(recipe)
    db_session.flush()
    _add_ingredient_line(
        db_session,
        recipe,
        canonical_name="scheduler_fresh_chicken",
        food_group="meat",
        quantity=300,
    )
    db_session.commit()

    if db_session.get(PlanningRule, DEFAULT_PLANNING_RULE_ID) is None:
        db_session.add(
            PlanningRule(id=DEFAULT_PLANNING_RULE_ID, name="Default", rules=DEFAULT_PLANNING_RULES_JSON, active=True)
        )
    if db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID) is None:
        db_session.add(SchedulerSettings(id=SCHEDULER_SETTINGS_ID, enabled=False))
    db_session.commit()

    candidates = load_dish_candidates(db_session, rules=PlanningRulesConfig.model_validate(DEFAULT_PLANNING_RULES_JSON))
    match = next(item for item in candidates if item.dish_id == dish.id)
    assert match.computed_traits_json is not None
    assert match.computed_traits_json["contains_meat"] is True
    assert "meat" in match.computed_traits_json["contains_food_groups"]


def test_slug_keeps_common_letters_and_strips_accents():
    assert "aioli" in slug_from_dish_name("Aïoli Sauce")
    assert "oliveoil" in slug_from_dish_name("Olive Oil Pasta")
    slug = slug_from_dish_name("Lentil Soup")
    for letter in "iou":
        assert letter in slug


def test_dish_public_key_suffix_uses_ambiguity_safe_alphabet():
    public_key = generate_dish_public_key("Spaghetti Puttanesca")
    assert validate_dish_public_key(public_key)
    suffix = public_key.split("-", 1)[1]
    assert all(char in PUBLIC_KEY_ALPHABET for char in suffix)
