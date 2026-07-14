from __future__ import annotations

from mealroulette.services.scheduler.pair_diagnostics import (
    SimpleDishSemanticRole,
    derive_simple_dish_semantic_role,
    food_group_weight,
    protein_share,
)
from mealroulette.services.scheduler.types import DishCandidate

__all__ = [
    "candidate_semantic_role",
    "candidate_traits",
    "food_group_weight",
    "protein_share",
]


def candidate_traits(candidate: DishCandidate) -> dict:
    return candidate.computed_traits_json or {}


def candidate_semantic_role(candidate: DishCandidate) -> SimpleDishSemanticRole | None:
    if candidate.pair_summary is not None and candidate.pair_summary.semantic_role is not None:
        return candidate.pair_summary.semantic_role
    return derive_simple_dish_semantic_role(
        candidate.computed_traits_json,
        simple_dish_part=candidate.simple_dish_part,
        tag_names=candidate.tag_names,
    )
