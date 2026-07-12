from __future__ import annotations

import secrets

DISH_PUBLIC_KEY_LENGTH = 32
DISH_PUBLIC_KEY_MAX_SLUG_LENGTH = 20
DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH = 8
RECIPE_SEQUENCE_WIDTH = 3
PUBLIC_KEY_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"


def slug_from_dish_name(name: str) -> str:
    allowed = set(PUBLIC_KEY_ALPHABET)
    slug = "".join(char for char in name.strip().lower() if char in allowed)
    if not slug:
        slug = "dish"
    return slug[:DISH_PUBLIC_KEY_MAX_SLUG_LENGTH]


def _random_suffix(length: int) -> str:
    if length < DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH:
        raise ValueError("random suffix length below minimum")
    return "".join(secrets.choice(PUBLIC_KEY_ALPHABET) for _ in range(length))


def generate_dish_public_key(name: str) -> str:
    slug = slug_from_dish_name(name)
    suffix_length = DISH_PUBLIC_KEY_LENGTH - len(slug) - 1
    if suffix_length < DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH:
        slug = slug[: DISH_PUBLIC_KEY_LENGTH - DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH - 1]
        suffix_length = DISH_PUBLIC_KEY_LENGTH - len(slug) - 1
    return f"{slug}-{_random_suffix(suffix_length)}"


def generate_recipe_public_key(dish_public_key: str, sequence_number: int) -> str:
    return f"{dish_public_key}-{sequence_number:0{RECIPE_SEQUENCE_WIDTH}d}"


def validate_dish_public_key(public_key: str) -> bool:
    if len(public_key) != DISH_PUBLIC_KEY_LENGTH:
        return False
    if public_key.count("-") != 1:
        return False
    slug, suffix = public_key.split("-", 1)
    if not slug or not suffix:
        return False
    if len(slug) > DISH_PUBLIC_KEY_MAX_SLUG_LENGTH:
        return False
    if len(suffix) < DISH_PUBLIC_KEY_MIN_RANDOM_LENGTH:
        return False
    allowed = set(PUBLIC_KEY_ALPHABET)
    return all(char in allowed for char in slug + suffix)


def validate_recipe_public_key(public_key: str, *, dish_public_key: str | None = None) -> bool:
    expected_length = DISH_PUBLIC_KEY_LENGTH + 1 + RECIPE_SEQUENCE_WIDTH
    if len(public_key) != expected_length:
        return False
    if dish_public_key is not None and not public_key.startswith(f"{dish_public_key}-"):
        return False
    suffix = public_key.rsplit("-", 1)[-1]
    if len(suffix) != RECIPE_SEQUENCE_WIDTH or not suffix.isdigit():
        return False
    return int(suffix) >= 1
