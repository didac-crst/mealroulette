"""Reconcile active ingredient seed with expanded proposal under ADR 001."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mealroulette.services.names import normalize_alias, normalize_name

DATA_DIR = Path(__file__).resolve().parent
ACTIVE_SEED_PATH = DATA_DIR / "fixtures" / "mealroulette_ingredients_seed.yaml"
ACTIVE_TAXONOMY_DIR = DATA_DIR / "taxonomy"
PROPOSAL_DIR = ACTIVE_TAXONOMY_DIR / "proposals"
PROPOSAL_SEED_PATH = PROPOSAL_DIR / "ingredients_seed_expanded_proposal.yaml"
PROPOSAL_FAMILIES_PATH = PROPOSAL_DIR / "ingredient_families.yaml"
PROPOSAL_FOOD_GROUPS_PATH = PROPOSAL_DIR / "food_groups.yaml"

# Rename active canonical -> survivor (old name becomes alias)
ACTIVE_CANONICAL_RENAMES: dict[str, str] = {
    "hake_fillet": "hake",
    "salmon_fillet": "salmon",
    "eggs": "egg",
    "calamari": "squid",
}

# Proposal canonical merges into active canonical (proposal row enriches active, not added separately)
PROPOSAL_TO_ACTIVE: dict[str, str] = {
    "passata": "tomato_passata",
    "courgette": "zucchini",
    "beef_mince": "minced_beef",
    "aioli": "allioli",
    "dukkah": "dukkah_spice",
}

# Proposal rows absorbed into another canonical then dropped
PROPOSAL_MERGE_INTO: dict[str, str] = {
    "fish_fumet": "fish_stock",
    "whipping_cream": "heavy_cream",
    "fiorelli_pasta": "stuffed_pasta",
    "ravioli": "stuffed_pasta",
    "fresh_thyme": "thyme",
    "fresh_sage": "sage",
    "coriander_leaves": "coriander",
    "lardons": "bacon",
    "white_beans": "cannellini_beans",
}

# Do not import proposal row — active or generic canonical is sufficient
DROP_PROPOSAL_CANONICAL: frozenset[str] = frozenset(
    {
        "yellow_onion",
        "hake_fillet",
        "salmon_fillet",
        "fresh_thyme",
        "flat_leaf_parsley",
        "courgette",
        "passata",
        "beef_mince",
        "aioli",
        "dukkah",
        "fish_fumet",
        "whipping_cream",
        "fiorelli_pasta",
        "ravioli",
        "fresh_sage",
        "coriander_leaves",
        "lardons",
        "white_beans",
    }
)

# When the same normalized alias appears on multiple canonical rows, keep only on the winner
ALIAS_OWNERSHIP: dict[str, str] = {
    normalize_alias("cilantro"): "coriander",
    normalize_alias("coriandre"): "coriander",
    normalize_alias("lentilles vertes"): "green_lentils",
    normalize_alias("green lentils"): "green_lentils",
    normalize_alias("heavy cream"): "heavy_cream",
    normalize_alias("lardons"): "bacon",
    normalize_alias("sage"): "sage",
    normalize_alias("thyme"): "thyme",
    normalize_alias("fiorelli"): "stuffed_pasta",
    normalize_alias("ravioli"): "stuffed_pasta",
    normalize_alias("cannellini beans"): "cannellini_beans",
}

# Aliases to remove globally (regionally ambiguous or policy)
REMOVE_ALIASES: frozenset[str] = frozenset(
    {
        normalize_alias("muslo de pollo"),
        normalize_alias("abadejo"),
    }
)

# Per-canonical alias removals after merges
CANONICAL_ALIAS_REMOVALS: dict[str, frozenset[str]] = {
    "quince_paste": frozenset({normalize_alias("membrillo")}),
}

# Per-canonical alias additions
CANONICAL_ALIAS_ADDITIONS: dict[str, list[str]] = {
    "quince": ["membrillo"],
    "quince_paste": ["dulce de membrillo", "carne de membrillo"],
    "zucchini": ["courgette"],
    "tomato_passata": ["passata", "tomato passata", "coulis de tomate"],
    "minced_beef": ["beef mince", "carne picada"],
    "allioli": ["aioli", "alioli"],
    "dukkah_spice": ["dukkah"],
    "squid": ["calamari"],
    "egg": ["eggs"],
    "hake": ["hake fillet"],
    "salmon": ["salmon fillet"],
    "fish_stock": ["fish fumet", "fumet de poisson", "fumet de pescado"],
    "heavy_cream": ["whipping cream", "nata para montar", "nata liquida"],
    "stuffed_pasta": ["fiorelli", "ravioli", "fiorelli pasta"],
    "thyme": ["fresh thyme"],
    "sage": ["fresh sage"],
    "coriander": ["cilantro", "coriandre", "coriander leaves"],
    "bacon": ["lardons"],
    "cream": ["single cream", "light cream"],
}

# Family fixes for empty or mis-assigned families
FAMILY_OVERRIDES: dict[str, str] = {
    "celery": "celery_family",
    "fennel_bulb": "fennel_family",
    "fennel_seeds": "spice_family",
    "avocado": "tropical_fruit_family",
    "mango": "tropical_fruit_family",
    "pineapple": "tropical_fruit_family",
    "plantain": "tropical_fruit_family",
}

# culinary_category when food_group differs from family default (condiment-like products)
CULINARY_CATEGORY_DEFAULTS: dict[str, str] = {
    "tomato_paste": "condiment",
    "sun_dried_tomato": "condiment",
    "peanut_butter": "condiment",
    "anchovy_paste": "condiment",
    "quince_paste": "condiment",
    "miso_paste": "condiment",
}

# storage_class defaults when pantry_item or preserved
SKIP_PROMOTION_REVIEW_STATUS = frozenset({"needs_human_review", "blocked"})


def _should_add_proposal_row(row: dict) -> bool:
    status = str(row.get("review_status") or "candidate").strip().lower()
    if status in SKIP_PROMOTION_REVIEW_STATUS:
        return False
    return True


@dataclass(frozen=True)
class ReconcileResult:
    ingredient_count: int
    families_count: int
    merged_from_proposal: int
    skipped_proposal: int
    renamed_active: int


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _merge_aliases(existing: list[str] | None, extra: list[str] | None) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for raw in (*(existing or []), *(extra or [])):
        text = str(raw).strip()
        if not text:
            continue
        key = normalize_alias(text)
        if key in REMOVE_ALIASES or key in seen:
            continue
        seen.add(key)
        merged.append(text)
    return merged


def _apply_metadata_defaults(row: dict) -> None:
    canonical = row["canonical_name"]
    if canonical in FAMILY_OVERRIDES:
        row["family"] = FAMILY_OVERRIDES[canonical]

    if row.get("culinary_category") is None and canonical in CULINARY_CATEGORY_DEFAULTS:
        row["culinary_category"] = CULINARY_CATEGORY_DEFAULTS[canonical]

    if row.get("storage_class") is None:
        if row.get("pantry_item"):
            row["storage_class"] = "ambient"
        elif row.get("category") == "vegetable" and not row.get("pantry_item"):
            row["storage_class"] = "fresh_produce"
        elif row.get("preservation") == "frozen":
            row["storage_class"] = "frozen"
        elif row.get("preservation") in {"fresh", None} and row.get("food_group") in {
            "meat",
            "fish",
            "seafood",
            "dairy",
            "egg",
        }:
            row["storage_class"] = "refrigerated"

    # Fix food_group pantry misuse -> semantic group from family (proposal already mostly fixed)
    if row.get("food_group") == "pantry" and row.get("family"):
        row.setdefault("storage_class", "ambient")
        row["pantry_item"] = True


def _merge_row(base: dict, incoming: dict) -> dict:
    result = copy.deepcopy(base)
    for field in (
        "display_name",
        "description",
        "category",
        "food_group",
        "family",
        "storage_class",
        "culinary_category",
        "product_form",
        "preservation",
        "default_recipe_unit",
        "preferred_shopping_unit",
        "aggregation_unit",
        "aggregation_strategy",
        "pantry_item",
        "review_status",
        "review_note",
    ):
        if incoming.get(field) is not None and (result.get(field) in (None, "", False) or field in incoming):
            if incoming.get(field) is not None:
                result[field] = incoming[field]

    if incoming.get("description") and (
        not result.get("description") or len(str(incoming["description"])) > len(str(result.get("description", "")))
    ):
        result["description"] = incoming["description"]

    result["aliases"] = _merge_aliases(result.get("aliases"), incoming.get("aliases"))
    if incoming.get("unit_conversions"):
        existing = {
            (c.get("from_unit"), c.get("to_unit")): c for c in (result.get("unit_conversions") or [])
        }
        for conv in incoming["unit_conversions"]:
            key = (conv.get("from_unit"), conv.get("to_unit"))
            if key not in existing:
                existing[key] = conv
        result["unit_conversions"] = list(existing.values())

    _apply_metadata_defaults(result)
    return result


def _enforce_alias_ownership(catalogue: dict[str, dict]) -> None:
    for canonical, row in catalogue.items():
        kept: list[str] = []
        for alias in row.get("aliases") or []:
            key = normalize_alias(alias)
            owner = ALIAS_OWNERSHIP.get(key)
            if owner is not None and owner != canonical:
                continue
            kept.append(alias)
        row["aliases"] = _merge_aliases(kept, None)


def reconcile_catalogue(
    *,
    active_seed_path: Path = ACTIVE_SEED_PATH,
    proposal_seed_path: Path = PROPOSAL_SEED_PATH,
    proposal_families_path: Path = PROPOSAL_FAMILIES_PATH,
    proposal_food_groups_path: Path = PROPOSAL_FOOD_GROUPS_PATH,
    active_taxonomy_dir: Path = ACTIVE_TAXONOMY_DIR,
) -> tuple[dict, dict, dict, ReconcileResult]:
    active_data = _load_yaml(active_seed_path)
    proposal_data = _load_yaml(proposal_seed_path)
    proposal_by_canonical = {row["canonical_name"]: row for row in proposal_data["ingredients"]}

    catalogue: dict[str, dict] = {}
    renamed_active = 0

    for row in active_data["ingredients"]:
        row = copy.deepcopy(row)
        canonical = row["canonical_name"]
        if canonical in ACTIVE_CANONICAL_RENAMES:
            new_canonical = ACTIVE_CANONICAL_RENAMES[canonical]
            row["aliases"] = _merge_aliases(row.get("aliases"), [canonical.replace("_", " "), canonical])
            row["canonical_name"] = new_canonical
            canonical = new_canonical
            renamed_active += 1
        if canonical in proposal_by_canonical:
            row = _merge_row(row, proposal_by_canonical[canonical])
        _apply_metadata_defaults(row)
        catalogue[canonical] = row

    merged = 0
    skipped = 0
    for canonical, row in proposal_by_canonical.items():
        if canonical in DROP_PROPOSAL_CANONICAL:
            skipped += 1
            continue
        target = PROPOSAL_TO_ACTIVE.get(canonical) or PROPOSAL_MERGE_INTO.get(canonical) or canonical
        if canonical in PROPOSAL_MERGE_INTO or canonical in PROPOSAL_TO_ACTIVE:
            if target not in catalogue:
                catalogue[target] = copy.deepcopy(row)
                catalogue[target]["canonical_name"] = target
            else:
                catalogue[target] = _merge_row(catalogue[target], row)
            merged += 1
            skipped += 1
            continue
        if canonical in catalogue:
            catalogue[canonical] = _merge_row(catalogue[canonical], row)
            merged += 1
            continue
        if not _should_add_proposal_row(row):
            skipped += 1
            continue
        new_row = copy.deepcopy(row)
        _apply_metadata_defaults(new_row)
        catalogue[canonical] = new_row
        merged += 1

    # Alias policy patches
    for canonical, row in catalogue.items():
        removals = CANONICAL_ALIAS_REMOVALS.get(canonical, frozenset())
        if removals:
            row["aliases"] = [
                alias
                for alias in row.get("aliases") or []
                if normalize_alias(alias) not in removals
            ]
        additions = CANONICAL_ALIAS_ADDITIONS.get(canonical)
        if additions:
            row["aliases"] = _merge_aliases(row.get("aliases"), additions)

    # Blocker fixes on surviving rows
    for name in ("chicken_leg", "chicken_thigh", "haddock", "pollock"):
        if name in catalogue:
            catalogue[name]["aliases"] = _merge_aliases(catalogue[name].get("aliases"), [])

    _enforce_alias_ownership(catalogue)

    # Drop merged-away canonicals if still present
    for drop in list(catalogue):
        if drop in PROPOSAL_MERGE_INTO and PROPOSAL_MERGE_INTO[drop] in catalogue and drop != PROPOSAL_MERGE_INTO[drop]:
            del catalogue[drop]
        if drop in {"fresh_thyme", "fresh_sage", "fiorelli_pasta", "ravioli", "lardons", "white_beans", "coriander_leaves"}:
            if drop in catalogue:
                del catalogue[drop]

    ingredients = sorted(catalogue.values(), key=lambda r: r["canonical_name"])
    used_families = {row["family"] for row in ingredients if row.get("family")}

    proposal_families = _load_yaml(proposal_families_path).get("ingredient_families") or []
    active_families = _load_yaml(active_taxonomy_dir / "ingredient_families.yaml").get("ingredient_families") or []
    proposal_family_by_id = {f["id"]: f for f in proposal_families}
    active_family_by_id = {f["id"]: f for f in active_families}

    merged_families: dict[str, dict] = dict(active_family_by_id)
    for family_id in used_families:
        if family_id in proposal_family_by_id:
            merged_families[family_id] = proposal_family_by_id[family_id]

    families_out = sorted(merged_families.values(), key=lambda f: f["id"])
    # Drop unused empty families from proposal that never got ingredients
    families_out = [f for f in families_out if f["id"] in used_families]

    food_groups_out = _load_yaml(proposal_food_groups_path)

    active_data["version"] = 3
    active_data["description"] = (
        "Reconciled canonical ingredient catalogue (ADR 001). Merged from active seed and validated proposal subset."
    )
    active_data["review_status"] = "reconciled_active"
    active_data["ingredients"] = ingredients

    families_yaml = {
        "version": 2,
        "name": "MealRoulette ingredient families",
        "description": "Families referenced by the reconciled active ingredient seed.",
        "ingredient_families": families_out,
    }

    result = ReconcileResult(
        ingredient_count=len(ingredients),
        families_count=len(families_out),
        merged_from_proposal=merged,
        skipped_proposal=skipped,
        renamed_active=renamed_active,
    )
    return active_data, families_yaml, food_groups_out, result


def write_reconciled_catalogue(
    *,
    active_seed_path: Path = ACTIVE_SEED_PATH,
    active_families_path: Path = ACTIVE_TAXONOMY_DIR / "ingredient_families.yaml",
    active_food_groups_path: Path = ACTIVE_TAXONOMY_DIR / "food_groups.yaml",
    **kwargs: Any,
) -> ReconcileResult:
    seed, families, food_groups, result = reconcile_catalogue(**kwargs)
    active_seed_path.write_text(yaml.dump(seed, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    active_families_path.write_text(
        yaml.dump(families, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )
    active_food_groups_path.write_text(
        yaml.dump(food_groups, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )
    return result
