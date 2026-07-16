import pytest
from sqlalchemy import select

from mealroulette.models.catalog import Dish, Ingredient, Recipe, Unit
from mealroulette.models.enums import DishCourse, DishStatus, RecipeType
from mealroulette.services.public_keys import (
    generate_dish_public_key,
    generate_recipe_public_key,
    validate_dish_public_key,
)
from mealroulette.services.scheduler.catalog import load_dish_candidates
from mealroulette.data.default_planning_rules import DEFAULT_PLANNING_RULES_JSON
from mealroulette.models.scheduler import PlanningRule, SchedulerSettings, DEFAULT_PLANNING_RULE_ID, SCHEDULER_SETTINGS_ID
from mealroulette.schemas.scheduler import PlanningRulesConfig


def _future_lunch_item(plan: dict, *, client=None, user_headers=None) -> dict:
    from datetime import date, timedelta

    today = date.today()
    for item in plan["items"]:
        if item["meal_slot"] == "lunch" and item["date"] > today.isoformat():
            return item
    if client is not None and user_headers is not None:
        week_start = date.fromisoformat(plan["week_start_date"])
        response = client.get(
            f"/api/meal-plans/{(week_start + timedelta(days=7)).isoformat()}",
            headers=user_headers,
        )
        if response.status_code == 200:
            for item in response.json()["items"]:
                if item["meal_slot"] == "lunch" and item["date"] > today.isoformat():
                    return item
    pytest.fail("expected a future lunch slot")


@pytest.mark.integration
def test_dish_public_key_stable_after_rename(client, catalog_seed, admin_headers):
    create = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Phase Nine Key Dish", "status": "active", "tag_ids": []},
    )
    assert create.status_code == 201
    dish = create.json()
    public_key = dish["public_key"]
    assert validate_dish_public_key(public_key)

    update = client.put(
        f"/api/dishes/{dish['id']}",
        headers=admin_headers,
        json={"name": "Renamed Phase Nine Dish"},
    )
    assert update.status_code == 200
    assert update.json()["public_key"] == public_key


@pytest.mark.integration
def test_recipe_sequences_and_traits_via_api(client, catalog_seed, admin_headers, db_session):
    gram = db_session.scalar(select(Unit).where(Unit.symbol == "g"))
    ingredient = Ingredient(
        canonical_name="phase9_chicken",
        display_name="Chicken",
        category="meat",
        food_group="meat",
        family="chicken_family",
    )
    db_session.add(ingredient)
    db_session.flush()

    dish_resp = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Phase Nine Traits Dish", "status": "active", "tag_ids": []},
    )
    dish_id = dish_resp.json()["id"]
    main = client.post(
        f"/api/dishes/{dish_id}/recipes",
        headers=admin_headers,
        json={"variant_name": "main", "is_main": True},
    ).json()
    alt = client.post(
        f"/api/dishes/{dish_id}/recipes",
        headers=admin_headers,
        json={"variant_name": "thermomix", "is_main": False},
    ).json()

    assert main["sequence_number"] == 1
    assert alt["sequence_number"] == 2
    assert main["public_key"].endswith("-001")
    assert alt["public_key"].endswith("-002")

    client.post(
        f"/api/recipes/{main['id']}/ingredients",
        headers=admin_headers,
        json={"ingredient_id": ingredient.id, "quantity": "300", "unit_id": gram.id},
    )
    recipe = client.get(f"/api/recipes/{main['id']}", headers=admin_headers).json()
    assert recipe["computed_traits_json"] is not None
    assert recipe["computed_traits_json"]["contains_meat"] is True

    dish = client.get(f"/api/dishes/{dish_id}", headers=admin_headers).json()
    assert dish["computed_traits_json"] is not None


@pytest.mark.integration
def test_meal_plan_item_effective_traits(client, catalog_seed, admin_headers, user_headers):
    dish_resp = client.post(
        "/api/dishes",
        headers=admin_headers,
        json={"name": "Plan Traits Dish", "status": "active", "tag_ids": []},
    )
    dish_id = dish_resp.json()["id"]
    recipe = client.post(
        f"/api/dishes/{dish_id}/recipes",
        headers=admin_headers,
        json={"variant_name": "main", "is_main": True},
    ).json()

    plan = client.get("/api/meal-plans/current", headers=user_headers).json()
    item = _future_lunch_item(plan, client=client, user_headers=user_headers)
    assign = client.post(
        "/api/meal-plan-items/assign",
        headers=user_headers,
        json={
            "date": item["date"],
            "meal_slot": item["meal_slot"],
            "dish_id": dish_id,
            "recipe_id": recipe["id"],
        },
    )
    assert assign.status_code == 200, assign.text
    payload = assign.json()
    assert payload["computed_traits_json"] is not None


@pytest.mark.integration
def test_scheduler_candidate_includes_traits(db_session, catalog_seed, scheduler_seed):
    dish = Dish(
        public_key=generate_dish_public_key("Scheduler Traits"),
        name="Scheduler Traits",
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
        computed_traits_json={"vegan": True, "contains_meat": False},
    )
    db_session.add(recipe)
    db_session.commit()

    if db_session.get(PlanningRule, DEFAULT_PLANNING_RULE_ID) is None:
        db_session.add(
            PlanningRule(
                id=DEFAULT_PLANNING_RULE_ID,
                name="default",
                active=True,
                rules_json=DEFAULT_PLANNING_RULES_JSON,
            )
        )
    if db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID) is None:
        db_session.add(SchedulerSettings(id=SCHEDULER_SETTINGS_ID))
    db_session.commit()

    rules = PlanningRulesConfig.model_validate(DEFAULT_PLANNING_RULES_JSON)
    candidates = load_dish_candidates(db_session, rules=rules)
    match = next(candidate for candidate in candidates if candidate.dish_id == dish.id)
    assert match.computed_traits_json is not None
    assert match.computed_traits_json["vegan"] is True
