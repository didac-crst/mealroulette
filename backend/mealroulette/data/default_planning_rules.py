"""Default scheduler planning rules seeded in migration 020."""

DEFAULT_PLANNING_RULES_JSON: dict = {
    "weekly_targets": {
        "fish": {"min": 1, "max": 2},
        "meat": {"min": 2, "max": 4},
        "vegetarian": {"min": 2, "max": 5},
        "pasta": {"min": 1, "max": 3},
        "rice": {"min": 1, "max": 3},
        "soup": {"min": 0, "max": 3},
    },
    "weekly_target_tolerance": 1,
    "avoid_same_dish_within_days": 21,
    "avoid_similar_meals_within_days": 14,
    "similarity_threshold": 0.75,
    "prefer_seasonal": True,
    "prefer_high_rated": True,
    "allow_leftovers": True,
    "default_grams_per_count": 100,
    "vector_min_grams": 5,
    "plan_attempts": 50,
    "history_window_days": 14,
    "composed_meals_per_week": {"min": 4, "max": 7},
    "structure_neutral_share": {"main": 0.60, "composed_pair": 0.40},
}

DEFAULT_PLANNING_RULE_NAME = "default"
