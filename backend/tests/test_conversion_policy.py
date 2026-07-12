"""Tests for ingredient conversion approval policy."""

from mealroulette.data.conversion_policy import (
    apply_conversion_policy_to_row,
    normalize_conversion_row,
)


def test_class1_unit_to_g_stays_unapproved():
    row = normalize_conversion_row(
        "avocado",
        {"from_unit": "unit", "to_unit": "g", "factor": 150, "confidence": "low"},
    )
    assert row["approved"] is False
    assert row["confidence"] == "approximate"


def test_exact_tbsp_ml_is_approved():
    row = normalize_conversion_row("capers", {"from_unit": "tbsp", "to_unit": "ml", "factor": 15})
    assert row["approved"] is True
    assert row["confidence"] == "exact"
    assert row["factor"] == 15


def test_normalize_conversion_row_writes_back_stripped_units():
    row = normalize_conversion_row("capers", {"from_unit": " tbsp ", "to_unit": " ml ", "factor": 15})
    assert row["from_unit"] == "tbsp"
    assert row["to_unit"] == "ml"


def test_herb_bunch_to_g_unapproved():
    row = normalize_conversion_row(
        "parsley",
        {"from_unit": "bunch", "to_unit": "g", "factor": 30, "confidence": "medium"},
    )
    assert row["approved"] is False
    assert row["confidence"] == "approximate"


def test_pastry_gets_sheet_form_and_unapproved_mass():
    ingredient = apply_conversion_policy_to_row(
        {
            "canonical_name": "puff_pastry",
            "unit_conversions": [{"from_unit": "unit", "to_unit": "g", "factor": 280}],
        }
    )
    assert ingredient["product_form"] == "sheet"
    assert ingredient["unit_conversions"][0]["approved"] is False


def test_capers_adds_exact_volume_conversion():
    ingredient = apply_conversion_policy_to_row(
        {
            "canonical_name": "capers",
            "unit_conversions": [{"from_unit": "tbsp", "to_unit": "g", "factor": 9}],
        }
    )
    pairs = {(c["from_unit"], c["to_unit"]) for c in ingredient["unit_conversions"]}
    assert ("tbsp", "ml") in pairs
    ml_row = next(c for c in ingredient["unit_conversions"] if c["to_unit"] == "ml")
    assert ml_row["approved"] is True
    g_row = next(c for c in ingredient["unit_conversions"] if c["to_unit"] == "g")
    assert g_row["approved"] is False
