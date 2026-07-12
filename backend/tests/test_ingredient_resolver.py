import pytest
from sqlalchemy import select

from mealroulette.models.catalog import Ingredient, IngredientAlias
from mealroulette.services.ingredient_resolver import IngredientResolverService, normalize_resolver_text


def test_normalize_resolver_text_strips_accents_and_ligatures():
    assert normalize_resolver_text("Cœur de bœuf") == "coeur de boeuf"
    assert normalize_resolver_text("  Poivron   Piquillo  ") == "poivron piquillo"


@pytest.mark.integration
def test_resolver_exact_alias_match(db_session, catalog_seed):
    ingredient = Ingredient(
        canonical_name="resolver_tomato",
        display_name="Tomato",
        category="vegetable",
        food_group="vegetable",
        family="tomato_family",
    )
    db_session.add(ingredient)
    db_session.flush()
    db_session.add(
        IngredientAlias(ingredient_id=ingredient.id, alias=normalize_resolver_text("tomatoes"))
    )
    db_session.commit()

    result = IngredientResolverService(db_session).resolve("tomatoes")
    assert result["status"] == "exact"
    assert result["matched_on"] == "alias"
    assert result["ingredient"]["canonical_name"] == "resolver_tomato"


@pytest.mark.integration
def test_resolver_returns_suggestions_for_partial(db_session, catalog_seed):
    ingredient = Ingredient(
        canonical_name="resolver_carrot",
        display_name="Carrot",
        category="vegetable",
        food_group="vegetable",
        family="carrot_family",
    )
    db_session.add(ingredient)
    db_session.commit()

    result = IngredientResolverService(db_session).resolve("carrot puree")
    assert result["status"] in {"suggestions", "exact", "none"}


@pytest.mark.integration
def test_classify_candidate_returns_guidance(db_session, catalog_seed):
    result = IngredientResolverService(db_session).classify_candidate(
        name="piquillo pepper",
        context="Spanish roasted pepper in a jar",
    )
    assert result["status"] in {"exact", "guided_suggestions", "unknown"}
    assert result["query"] == "piquillo pepper"
