from mealroulette.services.names import normalize_alias, normalize_name, to_canonical_slug


def test_to_canonical_slug_from_display_name():
    assert to_canonical_slug("Torch ginger flower") == "torch_ginger_flower"
    assert to_canonical_slug("Aji amarillo paste") == "aji_amarillo_paste"
    assert to_canonical_slug("torch_ginger_flower") == "torch_ginger_flower"


def test_proposal_normalized_name_keeps_spaces():
    assert normalize_name("Torch ginger flower") == "torch ginger flower"


def test_normalize_name_empty_and_whitespace():
    assert normalize_name("") == ""
    assert normalize_name("   ") == ""
    assert normalize_name("  torch   ginger  ") == "torch ginger"


def test_normalize_name_punctuation_and_case():
    assert normalize_name("Yuzu-Zest!") == "yuzu-zest!"
    assert normalize_name("AJÍ") == "ají"


def test_to_canonical_slug_accents_punctuation_and_empty():
    assert to_canonical_slug("") == ""
    assert to_canonical_slug("   ") == ""
    assert to_canonical_slug("  Aji   amarillo!! ") == "aji_amarillo"
    assert to_canonical_slug("café crème") == "cafe_creme"
    assert to_canonical_slug("œuf") == "oeuf"


def test_normalize_alias_collapses_punctuation_and_accents():
    assert normalize_alias("  Café-Crème!! ") == "cafe creme"
    assert normalize_alias("œufs") == "oeufs"
