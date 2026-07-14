from mealroulette.services.meal_plan_lines import compute_meal_title, primary_line, role_for_dish


def test_role_for_dish_main():
    from mealroulette.models.catalog import Dish
    from mealroulette.models.enums import MealComposition, MealPlanDishLineRole

    dish = Dish(name="Risotto", meal_composition=MealComposition.main_dish)
    assert role_for_dish(dish) == MealPlanDishLineRole.main


def test_role_for_dish_simple_parts():
    from mealroulette.models.catalog import Dish
    from mealroulette.models.enums import MealComposition, MealPlanDishLineRole, SimpleDishPart

    centerpiece = Dish(
        name="Beans",
        meal_composition=MealComposition.simple_dish,
        simple_dish_part=SimpleDishPart.centerpiece,
    )
    side = Dish(
        name="Ham croquettes",
        meal_composition=MealComposition.simple_dish,
        simple_dish_part=SimpleDishPart.sidedish,
    )
    assert role_for_dish(centerpiece) == MealPlanDishLineRole.centerpiece
    assert role_for_dish(side) == MealPlanDishLineRole.side


def test_compute_meal_title_simple_pair():
    from mealroulette.models.catalog import Dish
    from mealroulette.models.enums import (
        MealComposition,
        MealPlanDishLineRole,
        MealPlanDishLineSource,
        MealPlanningState,
        SimpleDishPart,
    )
    from mealroulette.models.planning import MealPlanItem, MealPlanItemDish

    item = MealPlanItem(planning_state=MealPlanningState.open)
    centerpiece_dish = Dish(name="Beans", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.centerpiece)
    side_dish = Dish(name="Ham croquettes", meal_composition=MealComposition.simple_dish, simple_dish_part=SimpleDishPart.sidedish)
    lines = [
        MealPlanItemDish(
            position=0,
            role=MealPlanDishLineRole.centerpiece,
            source=MealPlanDishLineSource.roulette,
            dish=centerpiece_dish,
        ),
        MealPlanItemDish(
            position=1,
            role=MealPlanDishLineRole.side,
            source=MealPlanDishLineSource.roulette,
            dish=side_dish,
        ),
    ]
    assert compute_meal_title(item, lines) == "Beans with Ham croquettes"


def test_compute_meal_title_multi_line():
    from mealroulette.models.catalog import Dish
    from mealroulette.models.enums import MealPlanDishLineRole, MealPlanDishLineSource, MealPlanningState
    from mealroulette.models.planning import MealPlanItem, MealPlanItemDish

    item = MealPlanItem(planning_state=MealPlanningState.open)
    main_dish = Dish(name="Pasta")
    dessert = Dish(name="Fruit crumble")
    lines = [
        MealPlanItemDish(position=0, role=MealPlanDishLineRole.main, source=MealPlanDishLineSource.roulette, dish=main_dish),
        MealPlanItemDish(position=1, role=MealPlanDishLineRole.dessert, source=MealPlanDishLineSource.manual, dish=dessert),
    ]
    assert compute_meal_title(item, lines) == "Pasta + Fruit crumble"


def test_primary_line_prefers_roulette_main():
    from mealroulette.models.catalog import Dish
    from mealroulette.models.enums import MealPlanDishLineRole, MealPlanDishLineSource
    from mealroulette.models.planning import MealPlanItemDish

    main = MealPlanItemDish(position=0, role=MealPlanDishLineRole.main, source=MealPlanDishLineSource.roulette, dish=Dish(name="Main"))
    extra = MealPlanItemDish(position=1, role=MealPlanDishLineRole.dessert, source=MealPlanDishLineSource.manual, dish=Dish(name="Dessert"))
    assert primary_line([extra, main]).role == MealPlanDishLineRole.main
