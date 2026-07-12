"""Validate taxonomy YAML and candidate/proposal ingredient rows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mealroulette.data.taxonomy_validator import validate_taxonomy, write_report

DEFAULT_TAXONOMY = Path(__file__).resolve().parents[1] / "data" / "taxonomy"
DEFAULT_PROPOSAL_TAXONOMY = DEFAULT_TAXONOMY / "proposals"
DEFAULT_CANDIDATES = DEFAULT_TAXONOMY.parent / "fixtures" / "mealroulette_ingredients_seed.yaml"
DEFAULT_ACTIVE_SEED = DEFAULT_CANDIDATES
DEFAULT_REPORT = Path(__file__).resolve().parents[3] / "docs" / "taxonomy" / "reports" / "taxonomy_validation_report.md"
DEFAULT_JSON_REPORT = Path(__file__).resolve().parents[3] / "docs" / "taxonomy" / "reports" / "taxonomy_validation_report.json"
DEFAULT_UNITS = DEFAULT_TAXONOMY.parent / "reference" / "units.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic taxonomy validation and write an exception report."
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=DEFAULT_TAXONOMY,
        help="Directory with food_groups.yaml and ingredient_families.yaml (default: active taxonomy)",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
        help="Ingredient seed YAML to validate (default: active fixtures seed)",
    )
    parser.add_argument(
        "--proposal",
        action="store_true",
        help="Validate proposal files instead of active seed",
    )
    parser.add_argument(
        "--active-seed",
        type=Path,
        default=DEFAULT_ACTIVE_SEED,
        help="Active canonical seed for alias collision checks",
    )
    parser.add_argument(
        "--active-taxonomy",
        type=Path,
        default=DEFAULT_TAXONOMY,
        help="Active taxonomy dir for new-family detection",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Markdown exception report output path",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=DEFAULT_JSON_REPORT,
        help="JSON report output path",
    )
    parser.add_argument(
        "--units",
        type=Path,
        action="append",
        default=[],
        help="Additional units YAML (repeatable). Reference units are always included.",
    )
    args = parser.parse_args()

    taxonomy_dir = DEFAULT_PROPOSAL_TAXONOMY if args.proposal else args.taxonomy
    candidates_path = (
        DEFAULT_PROPOSAL_TAXONOMY / "ingredients_seed_expanded_proposal.yaml"
        if args.proposal
        else args.candidates
    )
    active_seed = None if args.proposal else (args.active_seed if args.active_seed.is_file() else None)

    if not taxonomy_dir.is_dir():
        print(f"Taxonomy directory not found: {taxonomy_dir}", file=sys.stderr)
        sys.exit(1)
    if not candidates_path.is_file():
        print(f"Candidates file not found: {candidates_path}", file=sys.stderr)
        sys.exit(1)

    units_paths = [DEFAULT_UNITS, *args.units]
    active_taxonomy = args.active_taxonomy if args.active_taxonomy.is_dir() else None

    report = validate_taxonomy(
        taxonomy_dir=taxonomy_dir,
        candidates_path=candidates_path,
        active_seed_path=active_seed,
        active_taxonomy_dir=active_taxonomy,
        units_paths=units_paths,
    )
    write_report(report, markdown_path=args.report, json_path=args.json_report)

    print(f"Wrote report: {args.report}")
    print(f"Wrote JSON: {args.json_report}")
    print(
        "Summary: "
        f"{report.summary['candidates']} candidates, "
        f"{report.tier_counts['auto_accepted']} auto-accepted, "
        f"{report.tier_counts['needs_human_review']} needs review, "
        f"{report.tier_counts['blocked']} blocked, "
        f"{report.summary['blockers']} blocker findings"
    )

    if report.summary["blockers"] > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
