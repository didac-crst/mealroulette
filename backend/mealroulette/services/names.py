import re
import unicodedata

_LIGATURES = {"œ": "oe", "æ": "ae", "ß": "ss"}


def normalize_name(value: str) -> str:
    """Normalize display/alias text (lowercase, trimmed, collapsed spaces)."""
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_alias(value: str) -> str:
    """Normalize alias/resolver text: accents, ligatures, punctuation to spaces."""
    lowered = value.strip().lower()
    for source, target in _LIGATURES.items():
        lowered = lowered.replace(source, target)
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    collapsed = re.sub(r"[^a-z0-9]+", " ", without_accents)
    return re.sub(r"\s+", " ", collapsed).strip()


def to_canonical_slug(value: str) -> str:
    """Derive an internal snake_case canonical ingredient id from a display name."""
    aliased = normalize_alias(value)
    if not aliased:
        return ""
    return aliased.replace(" ", "_")
