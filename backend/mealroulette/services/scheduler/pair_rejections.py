from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from mealroulette.data.taxonomy_loader import family_to_food_group
from mealroulette.models.enums import SimpleDishPart
from mealroulette.services.food_groups import PROTEIN_FOOD_GROUPS
from mealroulette.services.scheduler.pair_diagnostics import (
    CENTERPIECE_PROTEIN_MIN_SHARE_PCT,
    SIDE_PROTEIN_MIN_SHARE_PCT,
    SimpleDishSemanticRole,
    derive_simple_dish_semantic_role,
)
from mealroulette.services.scheduler.types import DishCandidate

FAMILY_TO_FOOD_GROUP = family_to_food_group()

ANIMAL_PROTEIN_GROUPS = frozenset({"meat", "fish", "seafood", "egg"})
COMPETING_ANIMAL_PROTEIN_GROUPS = frozenset({"meat", "fish", "seafood", "egg"})


class PairRejectionCode(StrEnum):
    shared_primary_ingredient = "shared_primary_ingredient"
    duplicate_dominant_protein = "duplicate_dominant_protein"
    competing_animal_proteins = "competing_animal_proteins"
    primary_family_overlap = "primary_family_overlap"
    invalid_side_identity = "invalid_side_identity"


@dataclass(frozen=True)
class PairRejection:
    code: PairRejectionCode
    detail: str | None = None


@dataclass(frozen=True)
class PairHardRejectionResult:
    rejected: bool
    reasons: tuple[PairRejection, ...]


def _traits(candidate: DishCandidate) -> dict:
    return candidate.computed_traits_json or {}


def _semantic_role(candidate: DishCandidate) -> SimpleDishSemanticRole | None:
    if candidate.pair_summary is not None and candidate.pair_summary.semantic_role is not None:
        return candidate.pair_summary.semantic_role
    return derive_simple_dish_semantic_role(
        candidate.computed_traits_json,
        simple_dish_part=candidate.simple_dish_part,
        tag_names=candidate.tag_names,
    )


def _weight(traits: dict, group: str) -> float:
    weights = traits.get("food_group_weights")
    if not isinstance(weights, dict):
        return 0.0
    value = weights.get(group, 0.0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _protein_share(traits: dict) -> float:
    return sum(_weight(traits, group) for group in PROTEIN_FOOD_GROUPS)


def _normalize_animal_protein_group(group: str | None) -> str | None:
    if group is None:
        return None
    normalized = group.strip().lower()
    if normalized in {"fish", "seafood"}:
        return "fish"
    if normalized in ANIMAL_PROTEIN_GROUPS:
        return normalized
    return None


def _animal_protein_group_from_family(family_key: str | None) -> str | None:
    if not family_key:
        return None
    return _normalize_animal_protein_group(FAMILY_TO_FOOD_GROUP.get(family_key.strip().lower()))


def _dominant_animal_protein_group(candidate: DishCandidate) -> str | None:
    traits = _traits(candidate)
    dominant = traits.get("dominant_protein")
    if isinstance(dominant, str):
        group = _animal_protein_group_from_family(dominant)
        if group is not None:
            return group

    best_group: str | None = None
    best_share = 0.0
    for group in ("fish", "seafood", "meat", "egg"):
        share = _weight(traits, group)
        if share > best_share:
            best_group = _normalize_animal_protein_group(group)
            best_share = share
    return best_group


def _is_principal_animal_protein_identity(candidate: DishCandidate) -> bool:
    role = _semantic_role(candidate)
    if role in {
        SimpleDishSemanticRole.protein_centerpiece,
        SimpleDishSemanticRole.protein_side,
        SimpleDishSemanticRole.legume_centerpiece,
    }:
        return True
    if role in {
        SimpleDishSemanticRole.carb_centerpiece,
        SimpleDishSemanticRole.vegetable_centerpiece,
        SimpleDishSemanticRole.carb_side,
        SimpleDishSemanticRole.vegetable_side,
        SimpleDishSemanticRole.salad_side,
        SimpleDishSemanticRole.soup_side,
        SimpleDishSemanticRole.bread_side,
        SimpleDishSemanticRole.sauce_or_condiment,
    }:
        return False

    traits = _traits(candidate)
    threshold = (
        SIDE_PROTEIN_MIN_SHARE_PCT
        if candidate.simple_dish_part == SimpleDishPart.sidedish
        else CENTERPIECE_PROTEIN_MIN_SHARE_PCT
    )
    return _protein_share(traits) >= threshold and _dominant_animal_protein_group(candidate) is not None


def _primary_ingredient_ids(candidate: DishCandidate) -> frozenset[int]:
    if candidate.pair_summary is not None:
        return candidate.pair_summary.primary_ingredient_ids
    return frozenset()


def _primary_family_keys(candidate: DishCandidate) -> frozenset[str]:
    if candidate.pair_summary is not None:
        return candidate.pair_summary.primary_family_keys
    return frozenset()


def _shared_primary_ingredient_rejections(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> list[PairRejection]:
    centerpiece_ids = _primary_ingredient_ids(centerpiece)
    side_ids = _primary_ingredient_ids(side)
    if not centerpiece_ids or not side_ids:
        return []

    overlap = centerpiece_ids & side_ids
    if not overlap:
        return []
    return [
        PairRejection(
            code=PairRejectionCode.shared_primary_ingredient,
            detail=f"ingredient_ids={sorted(overlap)}",
        )
    ]


def _duplicate_dominant_protein_rejections(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> list[PairRejection]:
    centerpiece_traits = _traits(centerpiece)
    side_traits = _traits(side)
    centerpiece_dominant = centerpiece_traits.get("dominant_protein")
    side_dominant = side_traits.get("dominant_protein")

    if (
        isinstance(centerpiece_dominant, str)
        and isinstance(side_dominant, str)
        and centerpiece_dominant == side_dominant
    ):
        return [
            PairRejection(
                code=PairRejectionCode.duplicate_dominant_protein,
                detail=centerpiece_dominant,
            )
        ]

    if not _is_principal_animal_protein_identity(centerpiece) or not _is_principal_animal_protein_identity(side):
        return []

    centerpiece_group = _dominant_animal_protein_group(centerpiece)
    side_group = _dominant_animal_protein_group(side)
    if centerpiece_group is None or side_group is None:
        return []
    if centerpiece_group == side_group:
        return [
            PairRejection(
                code=PairRejectionCode.duplicate_dominant_protein,
                detail=centerpiece_group,
            )
        ]
    return []


def _competing_animal_proteins_rejections(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> list[PairRejection]:
    if not _is_principal_animal_protein_identity(centerpiece) or not _is_principal_animal_protein_identity(side):
        return []

    centerpiece_group = _dominant_animal_protein_group(centerpiece)
    side_group = _dominant_animal_protein_group(side)
    if centerpiece_group is None or side_group is None:
        return []
    if centerpiece_group == side_group:
        return []

    if (
        centerpiece_group in COMPETING_ANIMAL_PROTEIN_GROUPS
        and side_group in COMPETING_ANIMAL_PROTEIN_GROUPS
    ):
        return [
            PairRejection(
                code=PairRejectionCode.competing_animal_proteins,
                detail=f"{centerpiece_group}+{side_group}",
            )
        ]
    return []


def _primary_family_overlap_rejections(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> list[PairRejection]:
    centerpiece_families = _primary_family_keys(centerpiece)
    side_families = _primary_family_keys(side)
    if not centerpiece_families or not side_families:
        return []

    shared = centerpiece_families & side_families
    if not shared:
        return []

    side_contrast = side_families - centerpiece_families
    if side_contrast:
        return []

    return [
        PairRejection(
            code=PairRejectionCode.primary_family_overlap,
            detail=next(iter(sorted(shared))),
        )
    ]


def _invalid_side_identity_rejections(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> list[PairRejection]:
    side_role = _semantic_role(side)
    if side_role == SimpleDishSemanticRole.sauce_or_condiment:
        return [PairRejection(code=PairRejectionCode.invalid_side_identity, detail="sauce_or_condiment")]

    centerpiece_role = _semantic_role(centerpiece)
    if side_role == SimpleDishSemanticRole.soup_side and centerpiece_role == SimpleDishSemanticRole.soup_side:
        return [PairRejection(code=PairRejectionCode.invalid_side_identity, detail="dual_soup_structure")]

    centerpiece_tags = {tag.strip().lower() for tag in centerpiece.tag_names}
    if side_role == SimpleDishSemanticRole.salad_side and centerpiece_tags.intersection({"salad", "fresh", "raw"}):
        return [PairRejection(code=PairRejectionCode.invalid_side_identity, detail="dual_salad_structure")]

    return []


def evaluate_pair_hard_rejections(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> PairHardRejectionResult:
    reasons: list[PairRejection] = []
    reasons.extend(_shared_primary_ingredient_rejections(centerpiece, side))
    reasons.extend(_duplicate_dominant_protein_rejections(centerpiece, side))

    competing = _competing_animal_proteins_rejections(centerpiece, side)
    duplicate_codes = {entry.code for entry in reasons}
    if PairRejectionCode.duplicate_dominant_protein not in duplicate_codes:
        reasons.extend(competing)

    reasons.extend(_primary_family_overlap_rejections(centerpiece, side))
    reasons.extend(_invalid_side_identity_rejections(centerpiece, side))

    deduped: list[PairRejection] = []
    seen: set[tuple[PairRejectionCode, str | None]] = set()
    for reason in reasons:
        key = (reason.code, reason.detail)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(reason)

    return PairHardRejectionResult(rejected=bool(deduped), reasons=tuple(deduped))


def pair_is_hard_rejected(centerpiece: DishCandidate, side: DishCandidate) -> bool:
    return evaluate_pair_hard_rejections(centerpiece, side).rejected
