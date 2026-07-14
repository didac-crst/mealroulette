from __future__ import annotations

from dataclasses import dataclass

from mealroulette.services.food_groups import CARB_FOOD_GROUP, PROTEIN_FOOD_GROUPS
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.scheduler.pair_diagnostics import SimpleDishSemanticRole, derive_simple_dish_semantic_role
from mealroulette.services.scheduler.scoring import rating_score, score_candidate_for_slot, seasonality_score
from mealroulette.services.scheduler.types import DishCandidate, GenerationSlot, MealNeighbourSnapshot

COMPLEMENTARITY_BONUS = 0.75
POOR_COMPLEMENT_PENALTY = 0.5
WHOLE_MEAL_BALANCE_BONUS = 0.5
POOR_BALANCE_PENALTY = 0.45
DOMINANT_GROUP_PENALTY_THRESHOLD = 75.0
MEANINGFUL_GROUP_MIN_SHARE = 10.0
COMBINED_PROTEIN_HEAVY_THRESHOLD = 55.0
COMBINED_CARB_HEAVY_THRESHOLD = 60.0
STYLE_OVERLAP_PENALTY = 0.15
SHARED_FAMILY_SOFT_PENALTY = 0.2

MEANINGFUL_FOOD_GROUPS = frozenset(
    {"meat", "fish", "seafood", "egg", "dairy", "cheese", "legume", "plant_protein", "carbohydrate", "vegetable", "fruit"}
)

PREFERRED_SIDE_ROLES: dict[SimpleDishSemanticRole, frozenset[SimpleDishSemanticRole]] = {
    SimpleDishSemanticRole.protein_centerpiece: frozenset(
        {
            SimpleDishSemanticRole.vegetable_side,
            SimpleDishSemanticRole.salad_side,
            SimpleDishSemanticRole.carb_side,
            SimpleDishSemanticRole.bread_side,
            SimpleDishSemanticRole.soup_side,
        }
    ),
    SimpleDishSemanticRole.carb_centerpiece: frozenset(
        {
            SimpleDishSemanticRole.vegetable_side,
            SimpleDishSemanticRole.salad_side,
            SimpleDishSemanticRole.protein_side,
            SimpleDishSemanticRole.soup_side,
        }
    ),
    SimpleDishSemanticRole.vegetable_centerpiece: frozenset(
        {
            SimpleDishSemanticRole.protein_side,
            SimpleDishSemanticRole.carb_side,
            SimpleDishSemanticRole.bread_side,
        }
    ),
    SimpleDishSemanticRole.legume_centerpiece: frozenset(
        {
            SimpleDishSemanticRole.carb_side,
            SimpleDishSemanticRole.vegetable_side,
            SimpleDishSemanticRole.salad_side,
            SimpleDishSemanticRole.bread_side,
        }
    ),
}

AVOIDED_SIDE_ROLES: dict[SimpleDishSemanticRole, frozenset[SimpleDishSemanticRole]] = {
    SimpleDishSemanticRole.protein_centerpiece: frozenset({SimpleDishSemanticRole.protein_side}),
    SimpleDishSemanticRole.carb_centerpiece: frozenset({SimpleDishSemanticRole.carb_side}),
    SimpleDishSemanticRole.vegetable_centerpiece: frozenset(
        {SimpleDishSemanticRole.vegetable_side, SimpleDishSemanticRole.salad_side}
    ),
    SimpleDishSemanticRole.legume_centerpiece: frozenset({SimpleDishSemanticRole.protein_side}),
}


@dataclass(frozen=True)
class PairCompatibilityScore:
    adjustment: float
    reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]


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


def _combined_food_group_weights(centerpiece: DishCandidate, side: DishCandidate) -> dict[str, float]:
    combined_grams: dict[str, float] = {}
    for candidate in (centerpiece, side):
        traits = _traits(candidate)
        grams = traits.get("food_group_grams")
        if not isinstance(grams, dict):
            continue
        for group, amount in grams.items():
            if isinstance(amount, (int, float)):
                combined_grams[str(group)] = combined_grams.get(str(group), 0.0) + float(amount)

    total = sum(combined_grams.values())
    if total <= 0:
        return {}

    return {group: (amount / total) * 100.0 for group, amount in combined_grams.items()}


def _complementarity_reason(
    centerpiece: DishCandidate,
    centerpiece_role: SimpleDishSemanticRole,
    side_role: SimpleDishSemanticRole,
) -> str | None:
    traits = _traits(centerpiece)
    is_fish_centerpiece = _weight(traits, "fish") >= 25.0 or _weight(traits, "seafood") >= 25.0

    if centerpiece_role == SimpleDishSemanticRole.protein_centerpiece:
        if side_role in {SimpleDishSemanticRole.salad_side, SimpleDishSemanticRole.vegetable_side}:
            return "Adds a vegetable side"
        if side_role == SimpleDishSemanticRole.carb_side:
            if is_fish_centerpiece:
                return "Balances a fish centerpiece with a carb side"
            return "Adds a carb side to complete the meal"
        if side_role == SimpleDishSemanticRole.bread_side:
            return "Adds bread to round out the meal"
    if centerpiece_role == SimpleDishSemanticRole.carb_centerpiece and side_role in {
        SimpleDishSemanticRole.salad_side,
        SimpleDishSemanticRole.vegetable_side,
    }:
        return "Adds vegetables alongside the carb centerpiece"
    if centerpiece_role == SimpleDishSemanticRole.vegetable_centerpiece and side_role == SimpleDishSemanticRole.protein_side:
        return "Adds protein to a vegetable-forward centerpiece"
    if centerpiece_role == SimpleDishSemanticRole.legume_centerpiece and side_role == SimpleDishSemanticRole.carb_side:
        return "Pairs legumes with a carb side"
    if side_role in PREFERRED_SIDE_ROLES.get(centerpiece_role, frozenset()):
        return "Side complements the centerpiece role"
    return None


def _score_complementarity(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> tuple[float, list[str], list[str]]:
    centerpiece_role = _semantic_role(centerpiece)
    side_role = _semantic_role(side)
    if centerpiece_role is None or side_role is None:
        return 0.0, [], []

    reasons: list[str] = []
    codes: list[str] = []
    adjustment = 0.0

    preferred = PREFERRED_SIDE_ROLES.get(centerpiece_role, frozenset())
    avoided = AVOIDED_SIDE_ROLES.get(centerpiece_role, frozenset())

    if side_role in preferred:
        adjustment += COMPLEMENTARITY_BONUS
        codes.append("positive_complementarity")
        reason = _complementarity_reason(centerpiece, centerpiece_role, side_role)
        if reason:
            reasons.append(reason)

    if side_role in avoided:
        if centerpiece_role == SimpleDishSemanticRole.carb_centerpiece and side_role == SimpleDishSemanticRole.carb_side:
            if _traits(side).get("carb_heavy") or _weight(_traits(side), CARB_FOOD_GROUP) >= 30.0:
                adjustment -= POOR_COMPLEMENT_PENALTY
                reasons.append("Side repeats the carb focus of the centerpiece")
        elif centerpiece_role == SimpleDishSemanticRole.legume_centerpiece and _weight(_traits(side), "legume") >= 20.0:
            adjustment -= POOR_COMPLEMENT_PENALTY
            reasons.append("Side repeats the legume focus of the centerpiece")
        else:
            adjustment -= POOR_COMPLEMENT_PENALTY
            reasons.append("Side does not contrast enough with the centerpiece role")

    if centerpiece_role == SimpleDishSemanticRole.mixed_centerpiece:
        centerpiece_groups = {
            group
            for group in MEANINGFUL_FOOD_GROUPS
            if _weight(_traits(centerpiece), group) >= MEANINGFUL_GROUP_MIN_SHARE
        }
        side_groups = {
            group for group in MEANINGFUL_FOOD_GROUPS if _weight(_traits(side), group) >= MEANINGFUL_GROUP_MIN_SHARE
        }
        missing = side_groups - centerpiece_groups
        if missing:
            adjustment += COMPLEMENTARITY_BONUS * 0.5
            codes.append("positive_complementarity")
            reasons.append("Side adds a missing food group to the mixed centerpiece")

    return adjustment, reasons, codes


def _score_whole_meal_balance(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> tuple[float, list[str], list[str]]:
    combined = _combined_food_group_weights(centerpiece, side)
    if not combined:
        return 0.0, [], []

    reasons: list[str] = []
    codes: list[str] = []
    adjustment = 0.0

    meaningful = {
        group for group, share in combined.items() if group in MEANINGFUL_FOOD_GROUPS and share >= MEANINGFUL_GROUP_MIN_SHARE
    }
    dominant_group, dominant_share = max(combined.items(), key=lambda item: item[1])

    if len(meaningful) < 2:
        adjustment -= POOR_BALANCE_PENALTY
        reasons.append("Combined meal lacks enough food-group variety")
    elif len(meaningful) >= 3:
        adjustment += WHOLE_MEAL_BALANCE_BONUS
        codes.append("whole_meal_balance")
        reasons.append("Combines several food groups into a balanced meal")

    if dominant_share >= DOMINANT_GROUP_PENALTY_THRESHOLD:
        adjustment -= POOR_BALANCE_PENALTY
        reasons.append(f"One food group dominates the combined meal ({dominant_group})")

    protein_share = _protein_share({"food_group_weights": combined})
    carb_share = combined.get(CARB_FOOD_GROUP, 0.0)
    if protein_share >= COMBINED_PROTEIN_HEAVY_THRESHOLD:
        adjustment -= POOR_BALANCE_PENALTY * 0.5
        reasons.append("Combined meal is very protein-heavy")
    if carb_share >= COMBINED_CARB_HEAVY_THRESHOLD:
        adjustment -= POOR_BALANCE_PENALTY * 0.5
        reasons.append("Combined meal is very carb-heavy")

    has_protein = any(combined.get(group, 0.0) >= MEANINGFUL_GROUP_MIN_SHARE for group in PROTEIN_FOOD_GROUPS)
    has_carb = combined.get(CARB_FOOD_GROUP, 0.0) >= MEANINGFUL_GROUP_MIN_SHARE
    has_vegetable = combined.get("vegetable", 0.0) >= MEANINGFUL_GROUP_MIN_SHARE
    if has_protein and has_carb and has_vegetable and "whole_meal_balance" not in codes:
        adjustment += WHOLE_MEAL_BALANCE_BONUS
        codes.append("whole_meal_balance")
        reasons.append("Combines protein, carbs, and vegetables")

    return adjustment, reasons, codes


def _score_soft_overlap_penalties(
    centerpiece: DishCandidate,
    side: DishCandidate,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    adjustment = 0.0

    centerpiece_families = (
        centerpiece.pair_summary.primary_family_keys if centerpiece.pair_summary is not None else frozenset()
    )
    side_families = side.pair_summary.primary_family_keys if side.pair_summary is not None else frozenset()
    shared = centerpiece_families & side_families
    if shared and (side_families - centerpiece_families):
        adjustment -= SHARED_FAMILY_SOFT_PENALTY
        reasons.append("Some ingredient families repeat across the pair")

    if centerpiece.style_tags and side.style_tags and centerpiece.style_tags & side.style_tags:
        adjustment -= STYLE_OVERLAP_PENALTY
        shared_styles = ", ".join(sorted(centerpiece.style_tags & side.style_tags))
        reasons.append(f"Similar cooking style ({shared_styles})")

    return adjustment, reasons


def score_pair_compatibility(centerpiece: DishCandidate, side: DishCandidate) -> PairCompatibilityScore:
    adjustment = 0.0
    reasons: list[str] = []
    codes: list[str] = []

    complement_adjustment, complement_reasons, complement_codes = _score_complementarity(centerpiece, side)
    adjustment += complement_adjustment
    reasons.extend(complement_reasons)
    codes.extend(complement_codes)

    balance_adjustment, balance_reasons, balance_codes = _score_whole_meal_balance(centerpiece, side)
    adjustment += balance_adjustment
    reasons.extend(balance_reasons)
    codes.extend(balance_codes)

    overlap_adjustment, overlap_reasons = _score_soft_overlap_penalties(centerpiece, side)
    adjustment += overlap_adjustment
    reasons.extend(overlap_reasons)

    deduped_reasons: list[str] = []
    seen_reasons: set[str] = set()
    for reason in reasons:
        if reason in seen_reasons:
            continue
        seen_reasons.add(reason)
        deduped_reasons.append(reason)

    deduped_codes: list[str] = []
    seen_codes: set[str] = set()
    for code in codes:
        if code in seen_codes:
            continue
        seen_codes.add(code)
        deduped_codes.append(code)

    return PairCompatibilityScore(
        adjustment=round(adjustment, 3),
        reasons=tuple(deduped_reasons),
        reason_codes=tuple(deduped_codes),
    )


SIDE_LIGHT_SCORE_WEIGHT = 0.25


def _score_side_light_for_pair(
    side: DishCandidate,
    slot: GenerationSlot,
    *,
    rules: PlanningRulesConfig,
) -> float:
    month = slot.meal_date.month
    season_score, _ = seasonality_score(side, month=month, prefer_seasonal=rules.prefer_seasonal)
    rating_component, _ = rating_score(side, prefer_high_rated=rules.prefer_high_rated)
    return season_score + rating_component


def composed_pair_score_from_prescored(
    centerpiece: DishCandidate,
    side: DishCandidate,
    *,
    centerpiece_score: float,
    centerpiece_payload: dict,
    slot: GenerationSlot,
    rules: PlanningRulesConfig,
) -> tuple[float, dict]:
    side_light = _score_side_light_for_pair(side, slot, rules=rules)
    pair_compatibility = score_pair_compatibility(centerpiece, side)
    total_score = centerpiece_score + (SIDE_LIGHT_SCORE_WEIGHT * side_light) + pair_compatibility.adjustment

    pair_reasons = list(pair_compatibility.reasons)
    if not pair_reasons:
        pair_reasons.append(f"Paired with {side.dish_name}")

    payload = {
        **centerpiece_payload,
        "reasons": [
            *centerpiece_payload.get("reasons", []),
            *pair_reasons,
        ],
        "score": round(total_score, 3),
        "package_type": "centerpiece_side",
        "pair_reason_codes": list(pair_compatibility.reason_codes),
    }
    return total_score, payload


def score_pair_for_slot(
    centerpiece: DishCandidate,
    side: DishCandidate,
    slot: GenerationSlot,
    *,
    assigned_dish_ids: list[int],
    candidates_by_id: dict[int, DishCandidate],
    neighbours: list[MealNeighbourSnapshot],
    rules: PlanningRulesConfig,
) -> tuple[float, dict]:
    centerpiece_score, centerpiece_payload = score_candidate_for_slot(
        centerpiece,
        slot,
        assigned_dish_ids=assigned_dish_ids,
        candidates_by_id=candidates_by_id,
        neighbours=neighbours,
        rules=rules,
    )
    side_light = _score_side_light_for_pair(side, slot, rules=rules)
    pair_compatibility = score_pair_compatibility(centerpiece, side)
    total_score = centerpiece_score + (SIDE_LIGHT_SCORE_WEIGHT * side_light) + pair_compatibility.adjustment

    pair_reasons = list(pair_compatibility.reasons)
    if not pair_reasons:
        pair_reasons.append(f"Paired with {side.dish_name}")

    payload = {
        **centerpiece_payload,
        "reasons": [
            *centerpiece_payload.get("reasons", []),
            *pair_reasons,
        ],
        "score": round(total_score, 3),
        "package_type": "centerpiece_side",
        "pair_reason_codes": list(pair_compatibility.reason_codes),
    }
    return total_score, payload
