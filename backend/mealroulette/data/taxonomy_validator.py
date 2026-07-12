"""Deterministic taxonomy validation for candidate and proposal ingredient rows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from mealroulette.data.taxonomy_loader import (
    FoodGroupDefinition,
    IngredientFamilyDefinition,
    family_to_food_group,
    food_group_ids,
    load_food_groups,
    load_ingredient_families,
)
from mealroulette.services.names import normalize_alias, normalize_name

_VALID_CONFIDENCES = frozenset(
    {"exact", "high", "medium", "low", "not_recommended", "approximate", "measured"}
)
_VALID_SOURCES = frozenset({"manual", "seed", "seed_suggestion", "llm_suggested"})
_SEMANTIC_FOOD_GROUPS = frozenset(
    {
        "vegetable",
        "carbohydrate",
        "meat",
        "fish",
        "seafood",
        "egg",
        "dairy",
        "cheese",
        "legume",
        "plant_protein",
        "fat",
        "condiment",
        "herb",
        "spice",
        "stock",
        "fruit",
        "fungus",
        "alcohol",
    }
)
_HIGH_PRIORITY = frozenset({"core", "common"})


@dataclass
class ValidationFinding:
    severity: str  # blocker | review | suggestion
    category: str
    ingredient: str | None
    field: str | None
    message: str
    risk_flags: list[str] = field(default_factory=list)


@dataclass
class TaxonomyValidationReport:
    taxonomy_dir: str
    candidates_path: str
    active_seed_path: str | None
    summary: dict[str, int]
    blockers: list[ValidationFinding]
    needs_human_review: list[ValidationFinding]
    suggestions: list[ValidationFinding]
    alias_collisions: list[ValidationFinding]
    suspicious_conversions: list[ValidationFinding]
    new_families: list[str]
    empty_families: list[str]
    tier_counts: dict[str, int]

    def to_json(self) -> dict[str, Any]:
        return {
            "taxonomy_dir": self.taxonomy_dir,
            "candidates_path": self.candidates_path,
            "active_seed_path": self.active_seed_path,
            "summary": self.summary,
            "tier_counts": self.tier_counts,
            "new_families": self.new_families,
            "empty_families": self.empty_families,
            "blockers": [asdict(item) for item in self.blockers],
            "needs_human_review": [asdict(item) for item in self.needs_human_review],
            "suggestions": [asdict(item) for item in self.suggestions],
            "alias_collisions": [asdict(item) for item in self.alias_collisions],
            "suspicious_conversions": [asdict(item) for item in self.suspicious_conversions],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Taxonomy Validation Report",
            "",
            "## Summary",
            "",
            f"- Taxonomy: `{self.taxonomy_dir}`",
            f"- Candidates: `{self.candidates_path}`",
        ]
        if self.active_seed_path:
            lines.append(f"- Active seed (collision check): `{self.active_seed_path}`")
        lines.extend(
            [
                "",
                "| Metric | Count |",
                "| --- | ---: |",
            ]
        )
        for key, value in self.summary.items():
            lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
        lines.extend(["", "## Review tiers", ""])
        for tier, count in sorted(self.tier_counts.items()):
            lines.append(f"- **{tier}**: {count}")
        if self.new_families:
            lines.extend(["", "## New families (not in active taxonomy)", ""])
            for family_id in self.new_families:
                lines.append(f"- `{family_id}`")
        if self.empty_families:
            lines.extend(["", "## Empty families (no candidate rows)", ""])
            for family_id in self.empty_families:
                lines.append(f"- `{family_id}`")
        lines.extend(["", _section("Blockers", self.blockers)])
        lines.extend(["", _section("Needs human review", self.needs_human_review)])
        lines.extend(["", _section("Alias collisions", self.alias_collisions)])
        lines.extend(["", _section("Suspicious conversions", self.suspicious_conversions)])
        if self.suggestions:
            lines.extend(["", _section("Suggestions", self.suggestions[:50])])
            if len(self.suggestions) > 50:
                lines.append(f"\n_…and {len(self.suggestions) - 50} more suggestions._")
        return "\n".join(lines) + "\n"


def _section(title: str, findings: list[ValidationFinding]) -> str:
    if not findings:
        return f"## {title}\n\n_None._"
    lines = [f"## {title}", ""]
    for item in findings[:100]:
        label = item.ingredient or "(taxonomy)"
        flags = f" `[{', '.join(item.risk_flags)}]`" if item.risk_flags else ""
        lines.append(f"- **{label}** ({item.severity}) — {item.message}{flags}")
    if len(findings) > 100:
        lines.append(f"\n_…and {len(findings) - 100} more._")
    return "\n".join(lines)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML file: {path}")
    return data


def _load_taxonomy_from_dir(taxonomy_dir: Path) -> tuple[list[FoodGroupDefinition], list[IngredientFamilyDefinition]]:
    import mealroulette.data.taxonomy_loader as loader

    original = loader.TAXONOMY_DIR
    loader.TAXONOMY_DIR = taxonomy_dir
    loader.load_food_groups.cache_clear()
    loader.load_ingredient_families.cache_clear()
    loader.food_group_ids.cache_clear()
    loader.family_ids.cache_clear()
    loader.family_to_food_group.cache_clear()
    try:
        return load_food_groups(), load_ingredient_families()
    finally:
        loader.TAXONOMY_DIR = original
        loader.load_food_groups.cache_clear()
        loader.load_ingredient_families.cache_clear()
        loader.food_group_ids.cache_clear()
        loader.family_ids.cache_clear()
        loader.family_to_food_group.cache_clear()


def _load_unit_symbols(*paths: Path | None) -> set[str]:
    symbols: set[str] = set()
    for path in paths:
        if path is None or not path.is_file():
            continue
        data = _load_yaml(path)
        for row in data.get("units") or []:
            if isinstance(row, dict) and row.get("symbol"):
                symbols.add(str(row["symbol"]).strip())
    return symbols


def _ingredient_key(row: dict, *, flat: bool) -> str:
    if flat:
        return normalize_alias(str(row.get("name") or ""))
    return normalize_name(str(row.get("canonical_name") or ""))


def _row_food_group(row: dict, *, flat: bool) -> str | None:
    raw = row.get("likely_food_group") if flat else row.get("food_group")
    if raw is None:
        return None
    return str(raw).strip().lower()


def _row_family(row: dict, *, flat: bool) -> str | None:
    raw = row.get("likely_family") if flat else row.get("family")
    if raw is None:
        return None
    return str(raw).strip().lower()


def _collect_active_aliases(rows: list[dict]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for row in rows:
        canonical = normalize_name(str(row["canonical_name"]))
        for candidate in (
            canonical,
            normalize_name(str(row.get("display_name") or "")),
            *(normalize_alias(str(alias)) for alias in row.get("aliases") or []),
        ):
            if candidate:
                aliases.setdefault(candidate, canonical)
    return aliases


def validate_taxonomy(
    *,
    taxonomy_dir: Path,
    candidates_path: Path,
    active_seed_path: Path | None = None,
    active_taxonomy_dir: Path | None = None,
    units_paths: list[Path] | None = None,
) -> TaxonomyValidationReport:
    food_groups, families = _load_taxonomy_from_dir(taxonomy_dir)
    group_ids = {group.id for group in food_groups}
    family_ids_set = {family.id for family in families}
    family_groups = {family.id: family.food_group for family in families}

    active_family_ids: set[str] = set()
    if active_taxonomy_dir and active_taxonomy_dir.is_dir():
        _, active_families = _load_taxonomy_from_dir(active_taxonomy_dir)
        active_family_ids = {family.id for family in active_families}

    candidate_data = _load_yaml(candidates_path)
    rows = candidate_data.get("ingredients") or []
    flat = rows and rows[0].get("name") is not None and rows[0].get("canonical_name") is None

    unit_paths = list(units_paths or [])
    unit_paths.extend([taxonomy_dir.parent / "reference" / "units.yaml", candidates_path])
    unit_symbols = _load_unit_symbols(*unit_paths)

    active_aliases: dict[str, str] = {}
    if active_seed_path and active_seed_path.is_file():
        active_rows = _load_yaml(active_seed_path).get("ingredients") or []
        active_aliases = _collect_active_aliases(active_rows)

    blockers: list[ValidationFinding] = []
    needs_human_review: list[ValidationFinding] = []
    suggestions: list[ValidationFinding] = []
    alias_collisions: list[ValidationFinding] = []
    suspicious_conversions: list[ValidationFinding] = []

    # Taxonomy-level duplicate checks
    if len(group_ids) != len(food_groups):
        blockers.append(
            ValidationFinding(
                severity="blocker",
                category="taxonomy",
                ingredient=None,
                field="food_groups",
                message="Duplicate food group IDs in taxonomy YAML",
            )
        )
    if len(family_ids_set) != len(families):
        blockers.append(
            ValidationFinding(
                severity="blocker",
                category="taxonomy",
                ingredient=None,
                field="ingredient_families",
                message="Duplicate ingredient family IDs in taxonomy YAML",
            )
        )

    canonical_names: set[str] = set()
    alias_index: dict[str, str] = {}
    per_ingredient_flags: dict[str, list[str]] = {}
    per_ingredient_review: dict[str, bool] = {}
    families_used: set[str] = set()

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(
                ValidationFinding(
                    severity="blocker",
                    category="schema",
                    ingredient=f"row[{index}]",
                    field=None,
                    message="Expected ingredient mapping",
                )
            )
            continue

        key = _ingredient_key(row, flat=flat)
        display = row.get("name") if flat else row.get("canonical_name")
        ingredient_label = str(display or key or f"row[{index}]")

        if not key:
            blockers.append(
                ValidationFinding(
                    severity="blocker",
                    category="required_field",
                    ingredient=ingredient_label,
                    field="canonical_name" if not flat else "name",
                    message="Missing canonical identity",
                )
            )
            continue

        canonical = normalize_name(key.replace(" ", "_")) if flat else normalize_name(key)
        if canonical in canonical_names:
            blockers.append(
                ValidationFinding(
                    severity="blocker",
                    category="duplicate_canonical",
                    ingredient=canonical,
                    field="canonical_name",
                    message=f"Duplicate canonical name (also at index {index})",
                    risk_flags=["alias_collision"],
                )
            )
        canonical_names.add(canonical)

        flags = [str(flag) for flag in row.get("risk_flags") or []]
        per_ingredient_flags[canonical] = flags
        review_status = str(row.get("review_status") or "candidate").strip().lower()
        per_ingredient_review[canonical] = review_status in {
            "needs_human_review",
            "blocked",
            "proposal_needs_human_review",
        }

        food_group = _row_food_group(row, flat=flat)
        family = _row_family(row, flat=flat)
        if family:
            families_used.add(family)

        if food_group and food_group not in group_ids:
            blockers.append(
                ValidationFinding(
                    severity="blocker",
                    category="invalid_food_group",
                    ingredient=canonical,
                    field="food_group",
                    message=f"Unknown food group `{food_group}`",
                )
            )

        if family and family not in family_ids_set:
            blockers.append(
                ValidationFinding(
                    severity="blocker",
                    category="invalid_family",
                    ingredient=canonical,
                    field="family",
                    message=f"Unknown family `{family}`",
                    risk_flags=["new_family"],
                )
            )
        elif family and food_group:
            expected = family_groups.get(family)
            if expected and food_group != expected and not row.get("culinary_category"):
                finding = ValidationFinding(
                    severity="review",
                    category="family_mismatch",
                    ingredient=canonical,
                    field="food_group",
                    message=(
                        f"food_group `{food_group}` does not match family default `{expected}` "
                        "(set culinary_category if intentional)"
                    ),
                    risk_flags=["family_mismatch", "food_group_mismatch"],
                )
                if str(row.get("review_status") or "").lower() != "approved_exception":
                    needs_human_review.append(finding)

        if food_group == "pantry" and family:
            semantic = family_groups.get(family)
            if semantic and semantic in _SEMANTIC_FOOD_GROUPS:
                finding = ValidationFinding(
                    severity="review",
                    category="pantry_food_group",
                    ingredient=canonical,
                    field="food_group",
                    message=(
                        f"Uses food_group `pantry` but family `{family}` implies semantic group `{semantic}` "
                        "(prefer semantic food_group + storage_class/pantry_item)"
                    ),
                    risk_flags=["pantry_flag_suspicious", "food_group_mismatch"],
                )
                needs_human_review.append(finding)

        if food_group == "other":
            suggestions.append(
                ValidationFinding(
                    severity="suggestion",
                    category="other_food_group",
                    ingredient=canonical,
                    field="food_group",
                    message="Ingredient classified as `other` — confirm before promotion",
                )
            )

        pantry_item = bool(row.get("pantry_item"))
        if pantry_item and food_group in _SEMANTIC_FOOD_GROUPS and not row.get("storage_class"):
            suggestions.append(
                ValidationFinding(
                    severity="suggestion",
                    category="storage_class",
                    ingredient=canonical,
                    field="storage_class",
                    message=f"pantry_item=true with semantic food_group `{food_group}` — consider adding storage_class",
                    risk_flags=["pantry_flag_suspicious"],
                )
            )

        if not flat:
            description = str(row.get("description") or "").strip()
            if not description:
                needs_human_review.append(
                    ValidationFinding(
                        severity="review",
                        category="missing_description",
                        ingredient=canonical,
                        field="description",
                        message="Missing description",
                    )
                )

        if not family and not pantry_item and food_group not in {None, "pantry", "other"}:
            needs_human_review.append(
                ValidationFinding(
                    severity="review",
                    category="missing_family",
                    ingredient=canonical,
                    field="family",
                    message="Missing family for non-pantry ingredient",
                    risk_flags=["new_family"],
                )
            )

        priority = str(row.get("priority") or "").strip().lower()
        alias_values = row.get("aliases") or []
        if flat and priority in _HIGH_PRIORITY and not alias_values:
            needs_human_review.append(
                ValidationFinding(
                    severity="review",
                    category="missing_aliases",
                    ingredient=canonical,
                    field="aliases",
                    message=f"High-priority candidate missing aliases (priority={priority})",
                )
            )

        alias_candidates = {normalize_alias(str(alias)) for alias in alias_values if str(alias).strip()}
        if not flat:
            alias_candidates.update(
                {
                    normalize_alias(canonical.replace("_", " ")),
                    normalize_alias(str(row.get("display_name") or "")),
                }
            )
        else:
            alias_candidates.add(normalize_alias(str(row.get("name") or "")))

        for alias in alias_candidates:
            if not alias:
                continue
            owner = alias_index.get(alias)
            if owner is not None and owner != canonical:
                finding = ValidationFinding(
                    severity="blocker" if not flat else "review",
                    category="duplicate_alias",
                    ingredient=canonical,
                    field="aliases",
                    message=f"Alias `{alias}` also used by `{owner}`",
                    risk_flags=["alias_collision"],
                )
                alias_collisions.append(finding)
                if finding.severity == "blocker":
                    blockers.append(finding)
                else:
                    needs_human_review.append(finding)
            alias_index[alias] = canonical

            active_owner = active_aliases.get(alias)
            if active_owner is not None and active_owner != canonical:
                finding = ValidationFinding(
                    severity="review",
                    category="active_alias_collision",
                    ingredient=canonical,
                    field="aliases",
                    message=f"Alias `{alias}` collides with active seed ingredient `{active_owner}`",
                    risk_flags=["alias_collision"],
                )
                alias_collisions.append(finding)
                needs_human_review.append(finding)

        if not flat:
            for conv_index, conversion in enumerate(row.get("unit_conversions") or []):
                if not isinstance(conversion, dict):
                    continue
                from_unit = str(conversion.get("from_unit") or "").strip()
                to_unit = str(conversion.get("to_unit") or "").strip()
                if from_unit not in unit_symbols or to_unit not in unit_symbols:
                    blockers.append(
                        ValidationFinding(
                            severity="blocker",
                            category="invalid_unit",
                            ingredient=canonical,
                            field="unit_conversions",
                            message=f"Conversion {conv_index}: unknown unit symbol ({from_unit} -> {to_unit})",
                            risk_flags=["conversion_suspicious"],
                        )
                    )
                try:
                    factor = Decimal(str(conversion.get("factor")))
                    if factor <= 0:
                        raise InvalidOperation
                except (InvalidOperation, TypeError):
                    blockers.append(
                        ValidationFinding(
                            severity="blocker",
                            category="invalid_conversion",
                            ingredient=canonical,
                            field="unit_conversions",
                            message=f"Conversion {conv_index}: non-positive or missing factor",
                            risk_flags=["conversion_suspicious"],
                        )
                    )
                confidence = str(conversion.get("confidence") or "medium").strip().lower()
                if confidence not in _VALID_CONFIDENCES:
                    blockers.append(
                        ValidationFinding(
                            severity="blocker",
                            category="invalid_conversion",
                            ingredient=canonical,
                            field="unit_conversions",
                            message=f"Conversion {conv_index}: invalid confidence `{confidence}`",
                        )
                    )
                source = str(conversion.get("source") or "seed").strip().lower()
                if source not in _VALID_SOURCES:
                    blockers.append(
                        ValidationFinding(
                            severity="blocker",
                            category="invalid_conversion",
                            ingredient=canonical,
                            field="unit_conversions",
                            message=f"Conversion {conv_index}: invalid source `{source}`",
                        )
                    )
                approved = conversion.get("approved")
                if approved is True and confidence in {"low", "approximate", "not_recommended"}:
                    suspicious_conversions.append(
                        ValidationFinding(
                            severity="review",
                            category="conversion_approval",
                            ingredient=canonical,
                            field="unit_conversions",
                            message=f"Conversion {conv_index}: approved=true with low-confidence `{confidence}`",
                            risk_flags=["conversion_suspicious", "conversion_high_impact"],
                        )
                    )
                if approved is not False and confidence in {"low", "approximate"}:
                    suspicious_conversions.append(
                        ValidationFinding(
                            severity="suggestion",
                            category="conversion_approval",
                            ingredient=canonical,
                            field="unit_conversions",
                            message=f"Conversion {conv_index}: approximate conversion should usually stay unapproved",
                            risk_flags=["conversion_suspicious"],
                        )
                    )

        for flag in flags:
            if flag and flag not in {"pantry_item"}:
                needs_human_review.append(
                    ValidationFinding(
                        severity="review",
                        category="risk_flag",
                        ingredient=canonical,
                        field="risk_flags",
                        message=f"Candidate carries risk flag `{flag}`",
                        risk_flags=[flag],
                    )
                )

    new_families = sorted(family_ids_set - active_family_ids) if active_family_ids else []
    empty_families = sorted(family_ids_set - families_used)

    tier_counts = {"auto_accepted": 0, "needs_human_review": 0, "blocked": 0}
    blocker_keys = {item.ingredient for item in blockers if item.ingredient}
    review_keys = {item.ingredient for item in needs_human_review if item.ingredient}

    for canonical in canonical_names:
        if canonical in blocker_keys or per_ingredient_review.get(canonical):
            if canonical in blocker_keys:
                tier_counts["blocked"] += 1
            else:
                tier_counts["needs_human_review"] += 1
        elif canonical in review_keys or per_ingredient_flags.get(canonical):
            tier_counts["needs_human_review"] += 1
        else:
            tier_counts["auto_accepted"] += 1

    summary = {
        "candidates": len(rows),
        "food_groups": len(food_groups),
        "families": len(families),
        "blockers": len(blockers),
        "needs_human_review": len(needs_human_review),
        "suggestions": len(suggestions),
        "alias_collisions": len(alias_collisions),
        "suspicious_conversions": len(suspicious_conversions),
        "auto_accepted": tier_counts["auto_accepted"],
    }

    return TaxonomyValidationReport(
        taxonomy_dir=str(taxonomy_dir),
        candidates_path=str(candidates_path),
        active_seed_path=str(active_seed_path) if active_seed_path else None,
        summary=summary,
        blockers=blockers,
        needs_human_review=needs_human_review,
        suggestions=suggestions,
        alias_collisions=alias_collisions,
        suspicious_conversions=suspicious_conversions,
        new_families=new_families,
        empty_families=empty_families,
        tier_counts=tier_counts,
    )


def write_report(report: TaxonomyValidationReport, *, markdown_path: Path, json_path: Path | None = None) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_relativize_report(report).to_markdown(), encoding="utf-8")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(_relativize_report(report).to_json(), indent=2), encoding="utf-8")


def _relativize_report(report: TaxonomyValidationReport) -> TaxonomyValidationReport:
    """Use repo-relative paths in report output when possible."""
    try:
        repo_root = Path(__file__).resolve().parents[3]
    except IndexError:
        return report

    def _rel(path_str: str | None) -> str | None:
        if path_str is None:
            return None
        path = Path(path_str)
        try:
            return str(path.relative_to(repo_root))
        except ValueError:
            return path_str

    return TaxonomyValidationReport(
        taxonomy_dir=_rel(report.taxonomy_dir) or report.taxonomy_dir,
        candidates_path=_rel(report.candidates_path) or report.candidates_path,
        active_seed_path=_rel(report.active_seed_path) if report.active_seed_path else None,
        summary=report.summary,
        blockers=report.blockers,
        needs_human_review=report.needs_human_review,
        suggestions=report.suggestions,
        alias_collisions=report.alias_collisions,
        suspicious_conversions=report.suspicious_conversions,
        new_families=report.new_families,
        empty_families=report.empty_families,
        tier_counts=report.tier_counts,
    )
