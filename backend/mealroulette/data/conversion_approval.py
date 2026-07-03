"""Shared helpers for ingredient unit conversion approval from seed data."""


_BOOTSTRAP_CONFIDENCES = frozenset({"exact", "high", "medium"})


def resolve_conversion_approved(
    conversion_row: dict,
    ingredient_row: dict,
    *,
    bootstrap_approve: bool,
) -> bool:
    if conversion_row.get("approved") is True:
        return True
    if conversion_row.get("approved") is False:
        return False
    if not bootstrap_approve:
        return bool(conversion_row.get("approved"))
    strategy = ingredient_row.get("aggregation_strategy")
    confidence = conversion_row.get("confidence")
    if (
        strategy == "allow_approximate_conversion"
        and confidence in _BOOTSTRAP_CONFIDENCES
    ):
        return True
    return bool(conversion_row.get("approved"))
