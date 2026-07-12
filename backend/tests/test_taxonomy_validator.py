from pathlib import Path

import yaml

from mealroulette.data.taxonomy_validator import validate_taxonomy
from mealroulette.services.names import normalize_alias


def test_normalize_alias_strips_accents_and_ligatures():
    assert normalize_alias("Cœur de bœuf") == "coeur de boeuf"
    assert normalize_alias("pimentón ahumado") == "pimenton ahumado"
    assert normalize_alias("cherry_tomato") == "cherry tomato"


def test_validate_proposal_flags_pantry_food_group_for_tomato_family(tmp_path: Path):
    taxonomy_dir = tmp_path / "taxonomy"
    taxonomy_dir.mkdir()
    (taxonomy_dir / "food_groups.yaml").write_text(
        yaml.dump(
            {
                "food_groups": [
                    {"id": "vegetable", "label": "Vegetable", "description": "Vegetables"},
                    {"id": "pantry", "label": "Pantry", "description": "Pantry fallback"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (taxonomy_dir / "ingredient_families.yaml").write_text(
        yaml.dump(
            {
                "ingredient_families": [
                    {
                        "id": "tomato_family",
                        "food_group": "vegetable",
                        "label": "Tomato",
                        "description": "Tomatoes",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    candidates = tmp_path / "candidates.yaml"
    candidates.write_text(
        yaml.dump(
            {
                "ingredients": [
                    {
                        "canonical_name": "canned_tomatoes",
                        "display_name": "Canned tomatoes",
                        "description": "Canned product",
                        "food_group": "pantry",
                        "family": "tomato_family",
                        "aliases": ["tomate triturado"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = validate_taxonomy(taxonomy_dir=taxonomy_dir, candidates_path=candidates)
    assert any(item.category == "pantry_food_group" for item in report.needs_human_review)


def test_validate_detects_duplicate_alias(tmp_path: Path):
    taxonomy_dir = tmp_path / "taxonomy"
    taxonomy_dir.mkdir()
    (taxonomy_dir / "food_groups.yaml").write_text(
        yaml.dump({"food_groups": [{"id": "vegetable", "label": "Vegetable", "description": ""}]}),
        encoding="utf-8",
    )
    (taxonomy_dir / "ingredient_families.yaml").write_text(
        yaml.dump(
            {
                "ingredient_families": [
                    {"id": "tomato_family", "food_group": "vegetable", "label": "Tomato", "description": ""}
                ]
            }
        ),
        encoding="utf-8",
    )
    candidates = tmp_path / "candidates.yaml"
    candidates.write_text(
        yaml.dump(
            {
                "ingredients": [
                    {
                        "canonical_name": "tomato",
                        "display_name": "Tomato",
                        "description": "Fresh",
                        "food_group": "vegetable",
                        "family": "tomato_family",
                        "aliases": ["tomate"],
                    },
                    {
                        "canonical_name": "cherry_tomato",
                        "display_name": "Cherry tomato",
                        "description": "Small",
                        "food_group": "vegetable",
                        "family": "tomato_family",
                        "aliases": ["tomate"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = validate_taxonomy(taxonomy_dir=taxonomy_dir, candidates_path=candidates)
    assert report.alias_collisions
    assert report.summary["blockers"] >= 1
