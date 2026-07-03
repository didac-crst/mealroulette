"""Shared helpers for ingredient unit conversion approval from seed data."""


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
    confidence = conversion_row.get("confidence", "medium")
    if strategy == "allow_approximate_conversion" and confidence in {"exact", "high", "medium"}:
        return True
    return bool(conversion_row.get("approved"))
