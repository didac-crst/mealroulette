from mealroulette.core.errors import _json_safe_validation_errors


def test_json_safe_validation_errors_serializes_ctx_exception():
    errors = [
        {
            "type": "value_error",
            "loc": ("body",),
            "msg": "Value error, simple_dish_part is required",
            "input": {"meal_composition": "simple_dish"},
            "ctx": {"error": ValueError("simple_dish_part is required when meal_composition is simple_dish")},
        }
    ]

    serialized = _json_safe_validation_errors(errors)

    assert serialized[0]["ctx"]["error"] == (
        "simple_dish_part is required when meal_composition is simple_dish"
    )
