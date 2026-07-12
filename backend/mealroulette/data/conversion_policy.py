"""Ingredient unit conversion approval policy (ADR 001 supplement)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

# Class 1 — size/weight estimates; display only, not shopping aggregation.
CLASS1_SIZE_ESTIMATE: frozenset[str] = frozenset(
    {
        "avocado",
        "baguette",
        "cauliflower",
        "celery_stalk",
        "cherry_tomato",
        "chicken_breast",
        "coeur_de_boeuf_tomato",
        "firm_tofu",
        "green_chili",
        "hake",
        "kohlrabi",
        "leek",
        "portobello_mushroom",
        "pumpkin",
        "radish",
        "red_cabbage",
        "red_chili",
        "salmon",
        "sweet_potato",
        "sweetcorn",
    }
)

# Class 2 — approve only physically deterministic unit pairs (see EXACT_CONVERSION_FACTORS).
CLASS2_HERBS_SPICES_CITRUS: frozenset[str] = frozenset(
    {
        "chili_flakes",
        "coriander",
        "curry_powder",
        "dukkah_spice",
        "oregano",
        "parsley",
        "lemon",
        "lime",
        "spring_onion",
        "garlic",
    }
)

# Class 3 — package/sheet ingredients; avoid mass automation from count units.
CLASS3_PACKAGE_OR_DRAINED: frozenset[str] = frozenset(
    {
        "puff_pastry",
        "shortcrust_pastry",
        "capers",
    }
)

ALL_POLICY_INGREDIENTS = CLASS1_SIZE_ESTIMATE | CLASS2_HERBS_SPICES_CITRUS | CLASS3_PACKAGE_OR_DRAINED

# Deterministic conversions that may be approved (from_unit, to_unit) -> factor
EXACT_CONVERSION_FACTORS: dict[tuple[str, str], float] = {
    ("tbsp", "ml"): 15.0,
    ("tsp", "ml"): 5.0,
    ("kg", "g"): 1000.0,
    ("l", "ml"): 1000.0,
    ("ml", "l"): 0.001,
    ("g", "kg"): 0.001,
}

PRODUCT_FORM_OVERRIDES: dict[str, str] = {
    "puff_pastry": "sheet",
    "shortcrust_pastry": "sheet",
}

EXTRA_CONVERSIONS: dict[str, list[dict[str, Any]]] = {
    "capers": [
        {
            "from_unit": "tbsp",
            "to_unit": "ml",
            "factor": 15,
            "basis": "standard tablespoon volume (15 ml)",
            "confidence": "exact",
            "approved": True,
            "source": "seed",
        },
    ],
}


def _is_exact_pair(from_unit: str, to_unit: str) -> bool:
    return (from_unit.strip(), to_unit.strip()) in EXACT_CONVERSION_FACTORS


def normalize_conversion_row(canonical: str, conversion: dict[str, Any]) -> dict[str, Any]:
    """Apply approval policy to one conversion row."""
    row = deepcopy(conversion)
    from_unit = str(row.get("from_unit", "")).strip()
    to_unit = str(row.get("to_unit", "")).strip()
    row["from_unit"] = from_unit
    row["to_unit"] = to_unit

    if _is_exact_pair(from_unit, to_unit):
        expected = EXACT_CONVERSION_FACTORS[(from_unit, to_unit)]
        row["factor"] = expected
        row["confidence"] = "exact"
        row["approved"] = True
        row.setdefault("source", "seed")
        row.setdefault("basis", f"standard {from_unit} to {to_unit}")
        return row

    # All size/count/bunch/sheet/fillet estimates stay unapproved.
    row["confidence"] = "approximate"
    row["approved"] = False
    row.setdefault("source", "seed_suggestion")
    if canonical in CLASS3_PACKAGE_OR_DRAINED and from_unit in {"unit", "sheet"} and to_unit == "g":
        row["basis"] = (
            row.get("basis") or "sheet or unit mass varies by brand; display estimate only"
        )
    return row


def apply_conversion_policy_to_row(ingredient_row: dict[str, Any]) -> dict[str, Any]:
    """Return ingredient row with policy-normalized conversions and metadata."""
    row = deepcopy(ingredient_row)
    canonical = row["canonical_name"]
    if canonical not in ALL_POLICY_INGREDIENTS:
        return row

    if canonical in PRODUCT_FORM_OVERRIDES:
        row["product_form"] = PRODUCT_FORM_OVERRIDES[canonical]

    conversions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for conversion in row.get("unit_conversions") or []:
        normalized = normalize_conversion_row(canonical, conversion)
        key = (str(normalized["from_unit"]), str(normalized["to_unit"]))
        if key in seen:
            continue
        seen.add(key)
        conversions.append(normalized)

    for extra in EXTRA_CONVERSIONS.get(canonical, []):
        key = (str(extra["from_unit"]), str(extra["to_unit"]))
        if key not in seen:
            conversions.append(deepcopy(extra))
            seen.add(key)

    row["unit_conversions"] = conversions
    return row


def apply_conversion_policy_to_seed(path: Path | str) -> int:
    """Rewrite seed YAML in place. Returns count of ingredients updated."""
    seed_path = Path(path)
    data = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
    updated = 0
    ingredients: list[dict[str, Any]] = []
    for row in data["ingredients"]:
        new_row = apply_conversion_policy_to_row(row)
        if new_row != row:
            updated += 1
        ingredients.append(new_row)
    data["ingredients"] = ingredients
    seed_path.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    return updated
