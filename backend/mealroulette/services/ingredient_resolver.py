from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from mealroulette.data.taxonomy_loader import load_food_groups, load_ingredient_families
from mealroulette.models.catalog import Ingredient, IngredientAlias
from mealroulette.services.names import normalize_alias, normalize_name

AUTO_RESOLVE_SCORE = 0.95
AUTO_RESOLVE_GAP = 0.10
SUGGESTION_MIN_SCORE = 0.75
MAX_SUGGESTIONS = 10

AMBIGUOUS_TERMS = frozenset(
    {
        "cream",
        "cheese",
        "pepper",
        "rice",
        "noodles",
        "curry",
        "sauce",
        "fish",
        "beans",
    }
)


@dataclass(frozen=True)
class IndexedName:
    value: str
    normalized: str
    matched_on: str
    ingredient: Ingredient


def normalize_resolver_text(value: str) -> str:
    """Alias for normalize_alias — kept for resolver call sites and tests."""
    return normalize_alias(value)


def _compact(value: str) -> str:
    return value.replace(" ", "").replace("_", "")


def _score(query: str, candidate: str) -> float:
    if not query or not candidate:
        return 0.0
    if query == candidate:
        return 1.0
    if _compact(query) == _compact(candidate):
        return 0.98
    return SequenceMatcher(None, query, candidate).ratio()


def _token_overlap_score(query: str, candidate: str) -> float:
    query_tokens = set(query.split())
    candidate_tokens = set(candidate.split())
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens)
    return overlap / max(len(query_tokens), len(candidate_tokens))


def _combined_score(query: str, candidate: str) -> float:
    return max(_score(query, candidate), _token_overlap_score(query, candidate))


@dataclass
class IngredientResolverService:
    db: Session

    def _build_index(self) -> list[IndexedName]:
        entries: list[IndexedName] = []
        ingredients = self.db.scalars(select(Ingredient)).all()
        aliases = self.db.scalars(
            select(IngredientAlias).options(selectinload(IngredientAlias.ingredient))
        ).all()

        for ingredient in ingredients:
            for matched_on, raw in (
                ("canonical_name", ingredient.canonical_name),
                ("display_name", ingredient.display_name),
            ):
                normalized = normalize_resolver_text(raw.replace("_", " "))
                if normalized:
                    entries.append(
                        IndexedName(
                            value=raw,
                            normalized=normalized,
                            matched_on=matched_on,
                            ingredient=ingredient,
                        )
                    )
                compact = _compact(normalized)
                if compact and compact != normalized:
                    entries.append(
                        IndexedName(
                            value=raw,
                            normalized=compact,
                            matched_on=matched_on,
                            ingredient=ingredient,
                        )
                    )

        for alias_row in aliases:
            normalized = normalize_resolver_text(alias_row.alias)
            if not normalized:
                continue
            entries.append(
                IndexedName(
                    value=alias_row.alias,
                    normalized=normalized,
                    matched_on="alias",
                    ingredient=alias_row.ingredient,
                )
            )
        return entries

    @staticmethod
    def _to_match(ingredient: Ingredient, *, score: float | None = None) -> dict:
        return {
            "canonical_name": ingredient.canonical_name,
            "display_name": ingredient.display_name,
            "food_group": ingredient.food_group,
            "family": ingredient.family,
            "score": score,
        }

    def resolve(self, proposed_name: str) -> dict:
        query = proposed_name.strip()
        normalized = normalize_resolver_text(query)
        compact_query = _compact(normalized)

        index = self._build_index()
        for entry in index:
            if entry.normalized == normalized or entry.normalized == compact_query:
                return {
                    "status": "exact",
                    "query": query,
                    "matched_on": entry.matched_on,
                    "matched_value": entry.value,
                    "ingredient": self._to_match(entry.ingredient, score=1.0),
                    "suggestions": [],
                }

        scored: dict[int, tuple[float, IndexedName]] = {}
        for entry in index:
            score = _combined_score(normalized, entry.normalized)
            if score <= 0:
                continue
            ingredient_id = entry.ingredient.id
            current = scored.get(ingredient_id)
            if current is None or score > current[0]:
                scored[ingredient_id] = (score, entry)

        ranked = sorted(scored.values(), key=lambda item: item[0], reverse=True)
        if not ranked:
            return {"status": "none", "query": query, "suggestions": []}

        best_score, best_entry = ranked[0]
        second_score = ranked[1][0] if len(ranked) > 1 else 0.0
        is_ambiguous = normalized in AMBIGUOUS_TERMS or any(
            token in AMBIGUOUS_TERMS for token in normalized.split()
        )

        if (
            not is_ambiguous
            and best_score >= AUTO_RESOLVE_SCORE
            and (best_score - second_score) >= AUTO_RESOLVE_GAP
        ):
            return {
                "status": "exact",
                "query": query,
                "matched_on": best_entry.matched_on,
                "matched_value": best_entry.value,
                "ingredient": self._to_match(best_entry.ingredient, score=best_score),
                "suggestions": [],
            }

        suggestions = [
            self._to_match(entry.ingredient, score=score)
            for score, entry in ranked[:MAX_SUGGESTIONS]
            if score >= SUGGESTION_MIN_SCORE
        ]
        if suggestions:
            return {"status": "suggestions", "query": query, "suggestions": suggestions}
        return {"status": "none", "query": query, "suggestions": []}

    def classify_candidate(self, *, name: str, context: str | None = None, language: str | None = None) -> dict:
        del language  # reserved for future locale-aware ranking
        query_text = " ".join(part for part in [name, context or ""] if part).strip()
        normalized = normalize_resolver_text(query_text)
        tokens = set(normalized.split())

        food_group_scores: list[tuple[float, str, str]] = []
        for group in load_food_groups():
            haystack = normalize_resolver_text(f"{group.label} {group.description}")
            overlap = len(tokens & set(haystack.split()))
            if overlap:
                food_group_scores.append((overlap / max(len(tokens), 1), group.id, group.label))

        family_scores: list[tuple[float, str, str, str]] = []
        for family in load_ingredient_families():
            haystack = normalize_resolver_text(f"{family.label} {family.description}")
            overlap = len(tokens & set(haystack.split()))
            if overlap:
                family_scores.append(
                    (overlap / max(len(tokens), 1), family.id, family.food_group, family.label)
                )

        ingredient_scores: list[tuple[float, Ingredient, str]] = []
        pattern = f"%{normalized[:48]}%" if normalized else None
        ingredient_query = select(Ingredient)
        if pattern:
            ingredient_query = ingredient_query.where(
                or_(
                    func.lower(Ingredient.canonical_name).like(pattern),
                    func.lower(Ingredient.display_name).like(pattern),
                )
            ).limit(40)
        else:
            ingredient_query = ingredient_query.limit(0)

        for ingredient in self.db.scalars(ingredient_query):
            haystack = normalize_resolver_text(
                f"{ingredient.canonical_name} {ingredient.display_name} {ingredient.notes or ''}"
            )
            score = _combined_score(normalized, haystack)
            if score >= 0.4:
                ingredient_scores.append((score, ingredient, "Name or description overlap"))

        food_group_scores.sort(key=lambda item: item[0], reverse=True)
        family_scores.sort(key=lambda item: item[0], reverse=True)
        ingredient_scores.sort(key=lambda item: item[0], reverse=True)

        resolve_result = self.resolve(name)
        if resolve_result.get("status") == "exact" and resolve_result.get("ingredient"):
            return {
                "status": "exact",
                "query": name,
                "food_groups": [],
                "families": [],
                "ingredients": [
                    {
                        "canonical_name": resolve_result["ingredient"]["canonical_name"],
                        "display_name": resolve_result["ingredient"]["display_name"],
                        "family": resolve_result["ingredient"]["family"],
                        "food_group": resolve_result["ingredient"]["food_group"],
                        "reason": "Exact catalog match",
                        "score": resolve_result["ingredient"].get("score"),
                    }
                ],
                "draft": None,
            }

        top_families = family_scores[:5]
        top_groups = food_group_scores[:3]
        top_ingredients = [
            {
                "canonical_name": ingredient.canonical_name,
                "display_name": ingredient.display_name,
                "family": ingredient.family,
                "food_group": ingredient.food_group,
                "reason": reason,
                "score": score,
            }
            for score, ingredient, reason in ingredient_scores[:8]
        ]

        draft = None
        if not top_ingredients and top_families:
            family_id, food_group = top_families[0][1], top_families[0][2]
            canonical = re.sub(r"[^a-z0-9]+", "_", normalize_resolver_text(name)).strip("_") or "proposed_ingredient"
            draft = {
                "canonical_name": canonical,
                "display_name": name.strip(),
                "description": context,
                "food_group": food_group,
                "family": family_id,
                "aliases": [name.strip()],
                "unit_conversions": [],
                "review_status": "needs_human_review",
            }

        status = "guided_suggestions"
        if not top_groups and not top_families and not top_ingredients:
            status = "unknown"

        return {
            "status": status,
            "query": name,
            "food_groups": [
                {"id": group_id, "reason": f"Token overlap with {label} guidance.", "food_group": group_id}
                for _, group_id, label in top_groups
            ],
            "families": [
                {
                    "id": family_id,
                    "food_group": food_group,
                    "reason": f"Token overlap with {label} family guidance.",
                }
                for _, family_id, food_group, label in top_families
            ],
            "ingredients": top_ingredients,
            "draft": draft,
        }
