from mealroulette.services.names import normalize_name, to_canonical_slug


def test_to_canonical_slug_from_display_name():
    assert to_canonical_slug("Torch ginger flower") == "torch_ginger_flower"
    assert to_canonical_slug("Aji amarillo paste") == "aji_amarillo_paste"
    assert to_canonical_slug("torch_ginger_flower") == "torch_ginger_flower"


def test_proposal_normalized_name_keeps_spaces():
    assert normalize_name("Torch ginger flower") == "torch ginger flower"
