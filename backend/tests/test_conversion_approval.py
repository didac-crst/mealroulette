from mealroulette.data.conversion_approval import resolve_conversion_approved


def test_resolve_conversion_approved_honors_explicit_false_with_bootstrap():
    ingredient = {"aggregation_strategy": "allow_approximate_conversion"}
    conversion = {
        "confidence": "medium",
        "approved": False,
    }
    assert resolve_conversion_approved(conversion, ingredient, bootstrap_approve=True) is False


def test_resolve_conversion_approved_bootstraps_medium_approximate_conversion():
    ingredient = {"aggregation_strategy": "allow_approximate_conversion"}
    conversion = {"confidence": "medium"}
    assert resolve_conversion_approved(conversion, ingredient, bootstrap_approve=True) is True
