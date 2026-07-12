from __future__ import annotations

from mealroulette.schemas.scheduler import PlanningRulesConfig, WeeklyTargetSpec
from mealroulette.services.scheduler.types import DishCandidate

TARGET_TAG_GROUPS: dict[str, frozenset[str]] = {
    "vegetarian": frozenset({"legumes", "tofu_soy", "eggs", "cheese_dairy", "none_vegetables"}),
    "meat": frozenset({"chicken", "turkey", "beef", "pork", "lamb", "duck"}),
}


def dish_matches_weekly_target(candidate: DishCandidate, target_key: str) -> bool:
    if target_key in candidate.tag_names:
        return True
    alias_group = TARGET_TAG_GROUPS.get(target_key)
    if alias_group is not None:
        return bool(candidate.protein_tags & alias_group)
    return target_key in candidate.protein_tags | candidate.carb_tags | candidate.style_tags


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
