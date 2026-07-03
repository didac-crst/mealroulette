from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

REFERENCE_DIR = Path(__file__).parent / "reference"


@lru_cache
def load_ingredient_categories() -> list[dict[str, str]]:
    path = REFERENCE_DIR / "ingredient_categories.yaml"
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    rows = data.get("categories") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"Invalid ingredient categories file: {path}")
    categories: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or "id" not in row or "label" not in row:
            raise ValueError(f"Invalid category row in {path}: {row!r}")
        categories.append({"id": str(row["id"]), "label": str(row["label"])})
    return categories
