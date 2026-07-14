#!/usr/bin/env python3
"""Repair corrupted recipe step instructions and rewrite simple_dishes.yaml safely."""

from __future__ import annotations

from pathlib import Path

import yaml

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "mealroulette/data/fixtures/simple_dishes.yaml"


def _repair_step(step: object) -> dict:
    if not isinstance(step, dict):
        raise ValueError(f"Invalid recipe step entry: {step!r}")
    extra_keys = [key for key in step if key not in {"step_number", "instruction"}]
    if not extra_keys:
        instruction = step.get("instruction")
        if not isinstance(instruction, str):
            raise ValueError(f"Invalid instruction in step: {step!r}")
        return {"step_number": step["step_number"], "instruction": instruction}

    parts = [str(step.get("instruction", "")).strip()]
    for key in extra_keys:
        if step.get(key) is not None:
            raise ValueError(f"Unexpected non-null step field {key!r} in {step!r}")
        parts.append(str(key).strip())
    instruction = ", ".join(part for part in parts if part)
    return {"step_number": step["step_number"], "instruction": instruction}


def repair_fixture_data(data: dict) -> int:
    repaired = 0
    for dish in data.get("dishes", []):
        for recipe in dish.get("recipes", []):
            steps = recipe.get("steps")
            if not isinstance(steps, list):
                continue
            normalized_steps = []
            for step in steps:
                fixed = _repair_step(step)
                if fixed != step:
                    repaired += 1
                normalized_steps.append(fixed)
            recipe["steps"] = normalized_steps
    return repaired


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.nodes.ScalarNode:
    if any(marker in data for marker in ("\n", ":", ",", '"')):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def write_fixture(data: dict, path: Path = FIXTURE_PATH) -> None:
    yaml.add_representer(str, _represent_str, Dumper=yaml.SafeDumper)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )


def main() -> None:
    data = yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Fixture root must be a mapping")
    repaired = repair_fixture_data(data)
    write_fixture(data)
    print(f"Repaired {repaired} recipe steps in {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
