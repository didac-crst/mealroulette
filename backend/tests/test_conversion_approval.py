from mealroulette.data.conversion_approval import resolve_conversion_approved


def test_resolve_conversion_approved_honors_explicit_true():
    assert resolve_conversion_approved({"approved": True}, {}, bootstrap_approve=False) is True


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


def test_resolve_conversion_approved_without_bootstrap_defaults_to_false():
    ingredient = {"aggregation_strategy": "allow_approximate_conversion"}
    conversion = {"confidence": "high"}
    assert resolve_conversion_approved(conversion, ingredient, bootstrap_approve=False) is False


def test_resolve_conversion_approved_rejects_non_matching_strategy():
    ingredient = {"aggregation_strategy": "strict_same_dimension"}
    conversion = {"confidence": "exact"}
    assert resolve_conversion_approved(conversion, ingredient, bootstrap_approve=True) is False


def test_resolve_conversion_approved_skips_bootstrap_without_explicit_confidence():
    ingredient = {"aggregation_strategy": "allow_approximate_conversion"}
    conversion = {}
    assert resolve_conversion_approved(conversion, ingredient, bootstrap_approve=True) is False
