from __future__ import annotations

from mealroulette.schemas.scheduler import PlanningRulesConfig, WeeklyTargetSpec
from mealroulette.services.scheduler.types import DishCandidate

TARGET_TAG_GROUPS: dict[str, frozenset[str]] = {
    "vegetarian": frozenset({"legumes", "tofu_soy", "eggs", "cheese_dairy", "none_vegetables"}),
    "meat": frozenset({"chicken", "turkey", "beef", "pork", "lamb", "duck"}),
}

NON_DERIVABLE_TARGETS = frozenset({"soup"})


def _traits_match_weekly_target(traits: dict, target_key: str) -> bool:
    contains = set(traits.get("contains_food_groups") or [])
    family_vector = traits.get("family_vector") or {}
    dominant_carb = traits.get("dominant_carb")

    if target_key == "fish":
        return bool(contains & {"fish", "seafood"})
    if target_key == "meat":
        return bool(traits.get("contains_meat"))
    if target_key == "vegetarian":
        return not traits.get("contains_meat") and not (contains & {"fish", "seafood", "meat"})
    if target_key == "pasta":
        return dominant_carb == "pasta_family" or "pasta_family" in family_vector
    if target_key == "rice":
        return dominant_carb == "rice_family" or "rice_family" in family_vector
    if target_key in NON_DERIVABLE_TARGETS:
        return False
    return False


def _tags_match_weekly_target(candidate: DishCandidate, target_key: str) -> bool:
    if target_key in candidate.tag_names:
        return True
    alias_group = TARGET_TAG_GROUPS.get(target_key)
    if alias_group is not None:
        return bool(candidate.protein_tags & alias_group)
    return target_key in candidate.protein_tags | candidate.carb_tags | candidate.style_tags


def dish_matches_weekly_target(candidate: DishCandidate, target_key: str) -> bool:
    traits = candidate.computed_traits_json
    if isinstance(traits, dict) and _traits_match_weekly_target(traits, target_key):
        return True
    return _tags_match_weekly_target(candidate, target_key)


def count_weekly_target(
    target_key: str,
    dish_ids: list[int],
    *,
    candidates_by_id: dict[int, DishCandidate],
) -> int:
    count = 0
    for dish_id in dish_ids:
        candidate = candidates_by_id.get(dish_id)
        if candidate is not None and dish_matches_weekly_target(candidate, target_key):
            count += 1
    return count


def weekly_target_score_delta(
    candidate: DishCandidate,
    *,
    assigned_dish_ids: list[int],
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score_delta = 0.0

    for target_key, spec in rules.weekly_targets.items():
        current = count_weekly_target(target_key, assigned_dish_ids, candidates_by_id=candidates_by_id)
        projected = current + (1 if dish_matches_weekly_target(candidate, target_key) else 0)
        score_delta += _target_bucket_score(current, projected, spec, rules.weekly_target_tolerance)
        if projected >= spec.min and current < spec.min:
            reasons.append(f"Helps {target_key} target ({projected}/{spec.max} this week)")
        elif projected > spec.max + rules.weekly_target_tolerance:
            reasons.append(f"Would exceed {target_key} target ({projected}>{spec.max})")

    return score_delta, reasons


def weekly_target_warnings(
    assigned_dish_ids: list[int],
    *,
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
) -> list[str]:
    warnings: list[str] = []
    for target_key, spec in rules.weekly_targets.items():
        count = count_weekly_target(target_key, assigned_dish_ids, candidates_by_id=candidates_by_id)
        if count < spec.min - rules.weekly_target_tolerance:
            warnings.append(f"{target_key} target below minimum ({count}<{spec.min})")
        if count > spec.max + rules.weekly_target_tolerance:
            warnings.append(f"{target_key} target above maximum ({count}>{spec.max})")
    return warnings


def _target_bucket_score(
    current: int,
    projected: int,
    spec: WeeklyTargetSpec,
    tolerance: int,
) -> float:
    if projected > spec.max + tolerance:
        return -3.0
    if projected >= spec.min and current < spec.min:
        return 2.0
    if projected <= spec.max:
        return 0.5
    return -0.5
