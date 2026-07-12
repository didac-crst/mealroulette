from __future__ import annotations

import math


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0

    keys = left.keys() | right.keys()
    dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in keys)
    norm_left = math.sqrt(sum(value * value for value in left.values()))
    norm_right = math.sqrt(sum(value * value for value in right.values()))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)


def similarity_distance(left: dict[str, float], right: dict[str, float]) -> float:
    cosine = cosine_similarity(left, right)
    distance = 1.0 - cosine
    if distance < 0.0:
        return 0.0
    if distance > 1.0:
        return 1.0
    return distance


def shared_family_keys(
    left: dict[str, float],
    right: dict[str, float],
    *,
    min_pct: float = 0.0,
) -> list[str]:
    keys = left.keys() & right.keys()
    shared = [key for key in keys if left[key] >= min_pct and right[key] >= min_pct]
    return sorted(shared, key=lambda key: max(left[key], right[key]), reverse=True)
