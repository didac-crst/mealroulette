from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.models.catalog import Ingredient, IngredientAlias
from mealroulette.models.household import Household, HouseholdMembership, HouseholdRole
from mealroulette.models.ingredient_proposals import IngredientProposal
from mealroulette.models.user import User, UserRole


@pytest.fixture
def second_household(db_session: Session) -> Household:
    household = Household(id=uuid.uuid4(), name="Second household")
    db_session.add(household)
    db_session.commit()
    db_session.refresh(household)
    return household


@pytest.fixture
def second_household_user(db_session: Session, second_household: Household) -> User:
    user = User(
        username="other-household",
        email="other@example.com",
        password_hash=hash_password("otherpassword"),
        role=UserRole.user,
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        HouseholdMembership(
            household_id=second_household.id,
            user_id=user.id,
            role=HouseholdRole.household_member,
            active=True,
        )
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_household_headers(client: TestClient, second_household_user: User) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": second_household_user.username, "password": "otherpassword"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_proposal(client: TestClient, headers: dict[str, str], name: str = "yuzu zest", **extra):
    payload = {
        "proposed_name": name,
        "source_locale": "en",
        "description": "Citrus zest used in desserts",
        "culinary_context": "Japanese pastry",
        **extra,
    }
    return client.post("/api/ingredient-proposals", headers=headers, json=payload)


@pytest.mark.integration
def test_household_member_can_create_proposal(client, user_headers, catalog_seed):
    response = _create_proposal(client, user_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["proposal"]["proposed_name"] == "yuzu zest"
    assert body["proposal"]["normalized_name"] == "yuzu zest"
    assert body["proposal"]["resolution_status"] == "pending"
    assert body["proposal"]["resolved_ingredient_id"] is None
    assert isinstance(body["matches"], list)


@pytest.mark.integration
def test_user_lists_only_own_proposals(
    client,
    user_headers,
    second_household_headers,
    catalog_seed,
):
    mine = _create_proposal(client, user_headers, name="shiso leaf")
    other = _create_proposal(client, second_household_headers, name="perilla leaf")
    assert mine.status_code == 201
    assert other.status_code == 201

    listed = client.get("/api/ingredient-proposals/mine", headers=user_headers)
    assert listed.status_code == 200
    names = {item["proposed_name"] for item in listed.json()}
    assert names == {"shiso leaf"}
    assert all(item["proposed_by_user_id"] for item in listed.json())


@pytest.mark.integration
def test_user_cannot_read_other_proposal_private_provenance_via_matches(
    client,
    user_headers,
    second_household_headers,
    catalog_seed,
):
    first = _create_proposal(
        client,
        user_headers,
        name="black garlic paste",
        culinary_context="secret household note A",
        description="private description A",
    )
    assert first.status_code == 201

    second = _create_proposal(
        client,
        second_household_headers,
        name="black garlic paste",
        culinary_context="secret household note B",
        description="private description B",
    )
    assert second.status_code == 201
    matches = second.json()["matches"]
    pending = [match for match in matches if match["kind"] == "pending_proposal"]
    assert pending
    # Match list exposes only public aggregate labels, not culinary provenance.
    assert all("secret household" not in match["label"] for match in pending)
    assert any(match["label"] == "Similar pending proposal exists" for match in pending)
    # Other households' proposal UUIDs must not leak to members.
    assert all(match.get("proposal_id") in (None, "") for match in pending)
    first_id = first.json()["proposal"]["id"]
    assert all(match.get("proposal_id") != first_id for match in pending)


@pytest.mark.integration
def test_user_can_withdraw_own_pending_proposal(client, user_headers, catalog_seed):
    created = _create_proposal(client, user_headers, name="sumac powder")
    proposal_id = created.json()["proposal"]["id"]
    withdrawn = client.post(f"/api/ingredient-proposals/{proposal_id}/withdraw", headers=user_headers)
    assert withdrawn.status_code == 200
    assert withdrawn.json()["resolution_status"] == "withdrawn"


@pytest.mark.integration
def test_user_cannot_withdraw_terminal_proposal(client, user_headers, admin_headers, catalog_seed):
    created = _create_proposal(client, user_headers, name="fenugreek leaves")
    proposal_id = created.json()["proposal"]["id"]
    rejected = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/reject",
        headers=admin_headers,
        json={"review_note": "Not suitable"},
    )
    assert rejected.status_code == 200
    withdrawn = client.post(f"/api/ingredient-proposals/{proposal_id}/withdraw", headers=user_headers)
    assert withdrawn.status_code == 409


@pytest.mark.integration
def test_platform_admin_can_list_and_get_proposals(client, user_headers, admin_headers, catalog_seed):
    created = _create_proposal(client, user_headers, name="aji amarillo")
    proposal_id = created.json()["proposal"]["id"]

    listed = client.get("/api/platform/ingredient-proposals", headers=admin_headers)
    assert listed.status_code == 200
    assert any(item["id"] == proposal_id for item in listed.json())

    detail = client.get(f"/api/platform/ingredient-proposals/{proposal_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["culinary_context"] == "Japanese pastry"


@pytest.mark.integration
def test_non_platform_admin_cannot_review_proposals(client, user_headers, catalog_seed):
    created = _create_proposal(client, user_headers, name="gochugaru")
    proposal_id = created.json()["proposal"]["id"]
    response = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/reject",
        headers=user_headers,
        json={"review_note": "nope"},
    )
    assert response.status_code == 403


def _create_ingredient(client: TestClient, admin_headers: dict[str, str], name: str = "Tomato"):
    response = client.post(
        "/api/ingredients/confirm",
        headers=admin_headers,
        json={
            "action": "create",
            "proposed_name": name,
            "display_name": name,
            "category": "vegetable",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.integration
def test_map_existing_sets_resolved_ingredient(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
):
    ingredient = _create_ingredient(client, admin_headers, name="Mapped Base Ingredient")
    created = _create_proposal(client, user_headers, name="mapped zest")
    proposal_id = created.json()["proposal"]["id"]

    mapped = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/map-existing",
        headers=admin_headers,
        json={"ingredient_id": ingredient["id"], "review_note": "Already in catalog"},
    )
    assert mapped.status_code == 200
    body = mapped.json()
    assert body["resolution_status"] == "approved"
    assert body["resolution_type"] == "mapped_existing"
    assert body["resolved_ingredient_id"] == ingredient["id"]
    assert body["reviewed_by_user_id"] is not None
    assert body["reviewed_at"] is not None


@pytest.mark.integration
def test_add_alias_creates_alias_through_taxonomy_path(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
    db_session: Session,
):
    ingredient = _create_ingredient(client, admin_headers, name="Alias Base Ingredient")
    created = _create_proposal(client, user_headers, name="alias candidate xyz")
    proposal_id = created.json()["proposal"]["id"]

    aliased = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/add-alias",
        headers=admin_headers,
        json={"ingredient_id": ingredient["id"], "review_note": "Alias is fine"},
    )
    assert aliased.status_code == 200
    body = aliased.json()
    assert body["resolution_type"] == "added_alias"
    assert body["resolved_ingredient_id"] == ingredient["id"]

    alias = db_session.scalar(
        select(IngredientAlias).where(IngredientAlias.alias == "alias candidate xyz")
    )
    assert alias is not None
    assert alias.ingredient_id == ingredient["id"]


@pytest.mark.integration
def test_approve_new_creates_canonical_ingredient(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
    db_session: Session,
):
    created = _create_proposal(client, user_headers, name="Unique Canonical Root")
    proposal_id = created.json()["proposal"]["id"]

    approved = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/approve-new",
        headers=admin_headers,
        json={
            "display_name": "Unique Canonical Root",
            "food_group": "vegetable",
            "family": "tomato_family",
            "aliases": ["unique root alias"],
            "preferred_shopping_unit_id": None,
            "conversion_notes": "1 piece ≈ 20 g",
            "review_note": "New entry",
        },
    )
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["resolution_status"] == "approved"
    assert body["resolution_type"] == "created_canonical"
    assert body["resolved_ingredient_id"] is not None

    ingredient = db_session.get(Ingredient, body["resolved_ingredient_id"])
    assert ingredient is not None
    assert ingredient.canonical_name == "unique_canonical_root"
    assert ingredient.notes and "1 piece ≈ 20 g" in ingredient.notes
    alias = db_session.scalar(
        select(IngredientAlias).where(IngredientAlias.alias == "unique root alias")
    )
    assert alias is not None
    assert alias.ingredient_id == ingredient.id


@pytest.mark.integration
def test_rejected_proposal_does_not_block_future_submission(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
):
    created = _create_proposal(client, user_headers, name="Torch ginger flower")
    proposal_id = created.json()["proposal"]["id"]
    rejected = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/reject",
        headers=admin_headers,
        json={"review_note": "Needs better context"},
    )
    assert rejected.status_code == 200

    again = _create_proposal(
        client,
        user_headers,
        name="Torch ginger flower",
        description="Flower bud used in Malaysian laksa",
    )
    assert again.status_code == 201
    assert again.json()["proposal"]["resolution_status"] == "pending"
    assert again.json()["proposal"]["id"] != proposal_id


@pytest.mark.integration
def test_approve_new_blocks_existing_canonical_slug(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
):
    existing = _create_ingredient(client, admin_headers, name="torch_ginger_flower")
    # confirm path normalizes with spaces/underscores preserved for underscores
    assert existing["canonical_name"] in {"torch_ginger_flower", "torch ginger flower"}

    created = _create_proposal(client, user_headers, name="Torch ginger flower")
    proposal_id = created.json()["proposal"]["id"]
    assert any(match["kind"] in {"ingredient", "alias"} for match in created.json()["matches"])

    approved = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/approve-new",
        headers=admin_headers,
        json={
            "canonical_name": "torch_ginger_flower",
            "display_name": "Torch ginger flower",
            "food_group": "vegetable",
            "family": "tomato_family",
        },
    )
    assert approved.status_code == 409
    message = approved.json().get("error", {}).get("message") or approved.json().get("detail") or ""
    assert "map-existing" in message.lower() or "add-alias" in message.lower()


@pytest.mark.integration
def test_reject_request_information_and_duplicate_transitions(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
):
    created = _create_proposal(client, user_headers, name="needs more context")
    proposal_id = created.json()["proposal"]["id"]

    needs_info = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/request-information",
        headers=admin_headers,
        json={"review_note": "Which cultivar?"},
    )
    assert needs_info.status_code == 200
    assert needs_info.json()["resolution_status"] == "needs_information"

    provided = client.post(
        f"/api/ingredient-proposals/{proposal_id}/provide-information",
        headers=user_headers,
        json={"culinary_context": "Fresh cultivar from market", "review_response": "Fresh only"},
    )
    assert provided.status_code == 200
    assert provided.json()["resolution_status"] == "pending"

    duplicated = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/mark-duplicate",
        headers=admin_headers,
        json={"review_note": "Duplicate of another request"},
    )
    assert duplicated.status_code == 200
    assert duplicated.json()["resolution_status"] == "duplicate"

    created2 = _create_proposal(client, user_headers, name="reject me")
    proposal2 = created2.json()["proposal"]["id"]
    rejected = client.post(
        f"/api/platform/ingredient-proposals/{proposal2}/reject",
        headers=admin_headers,
        json={"review_note": "Out of scope"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["resolution_status"] == "rejected"
    assert rejected.json()["resolution_type"] == "rejected"


@pytest.mark.integration
def test_invalid_state_transitions_are_rejected(client, user_headers, admin_headers, catalog_seed):
    ingredient = _create_ingredient(client, admin_headers, name="Transition Base")
    created = _create_proposal(client, user_headers, name="terminal once")
    proposal_id = created.json()["proposal"]["id"]
    rejected = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/reject",
        headers=admin_headers,
        json={"review_note": "done"},
    )
    assert rejected.status_code == 200

    again = client.post(
        f"/api/platform/ingredient-proposals/{proposal_id}/map-existing",
        headers=admin_headers,
        json={"ingredient_id": ingredient["id"]},
    )
    assert again.status_code == 409


@pytest.mark.integration
def test_dedup_match_lookup_catches_ingredient_alias_and_pending(
    client,
    user_headers,
    second_household_headers,
    admin_headers,
    catalog_seed,
    db_session: Session,
):
    ingredient = _create_ingredient(client, admin_headers, name="Dedup Exact Ingredient")

    exact = _create_proposal(client, user_headers, name=ingredient["canonical_name"])
    assert exact.status_code == 201
    kinds = {match["kind"] for match in exact.json()["matches"]}
    assert "ingredient" in kinds

    alias = IngredientAlias(ingredient_id=ingredient["id"], alias="proposal alias match")
    db_session.add(alias)
    db_session.commit()

    alias_hit = _create_proposal(client, user_headers, name="Proposal Alias Match")
    assert alias_hit.status_code == 201
    assert any(match["kind"] == "alias" for match in alias_hit.json()["matches"])

    pending = _create_proposal(client, user_headers, name="shared pending name")
    assert pending.status_code == 201
    similar = _create_proposal(client, second_household_headers, name="shared pending name")
    assert similar.status_code == 201
    assert any(match["kind"] == "pending_proposal" for match in similar.json()["matches"])


@pytest.mark.integration
def test_create_does_not_mutate_catalog(client, user_headers, catalog_seed, db_session: Session):
    before = db_session.scalar(select(Ingredient).where(Ingredient.canonical_name == "brand new proposal only"))
    assert before is None
    created = _create_proposal(client, user_headers, name="Brand New Proposal Only")
    assert created.status_code == 201
    after = db_session.scalar(select(Ingredient).where(Ingredient.canonical_name == "brand new proposal only"))
    assert after is None
    assert db_session.scalar(select(IngredientProposal).limit(1)) is not None


@pytest.mark.integration
def test_user_facing_review_actions_require_non_empty_review_note(
    client,
    user_headers,
    admin_headers,
    catalog_seed,
):
    created = _create_proposal(client, user_headers, name="needs an explanation")
    proposal_id = created.json()["proposal"]["id"]

    for path, payload in (
        ("reject", {"review_note": ""}),
        ("reject", {"review_note": "   "}),
        ("reject", {}),
        ("request-information", {"review_note": ""}),
        ("request-information", {"review_note": "   "}),
        ("mark-duplicate", {"review_note": ""}),
        ("mark-duplicate", {"review_note": "   "}),
        ("mark-duplicate", {}),
    ):
        response = client.post(
            f"/api/platform/ingredient-proposals/{proposal_id}/{path}",
            headers=admin_headers,
            json=payload,
        )
        assert response.status_code == 422, (path, payload, response.text)

    detail = client.get(f"/api/platform/ingredient-proposals/{proposal_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["resolution_status"] == "pending"


@pytest.mark.integration
def test_add_alias_and_proposal_review_commit_atomically(
    client,
    user_headers,
    admin_headers,
    admin_user,
    catalog_seed,
    db_session: Session,
    monkeypatch,
):
    """Catalog alias must not persist if the proposal review update fails."""
    from mealroulette.schemas.ingredient_proposals import IngredientProposalAddAliasRequest
    from mealroulette.services.ingredient_proposals import IngredientProposalService

    ingredient = _create_ingredient(client, admin_headers, name="Atomic Alias Base")
    created = _create_proposal(client, user_headers, name="atomic alias candidate")
    proposal_id = uuid.UUID(created.json()["proposal"]["id"])

    def fail_review(self, *args, **kwargs):
        raise RuntimeError("forced review failure")

    monkeypatch.setattr(IngredientProposalService, "_apply_review", fail_review)
    service = IngredientProposalService(db_session)

    with pytest.raises(RuntimeError, match="forced review failure"):
        service.add_alias(
            proposal_id=proposal_id,
            reviewer=admin_user,
            payload=IngredientProposalAddAliasRequest(ingredient_id=ingredient["id"]),
        )

    db_session.rollback()

    proposal = db_session.get(IngredientProposal, proposal_id)
    assert proposal is not None
    assert proposal.resolution_status == "pending"
    assert proposal.resolved_ingredient_id is None
    assert (
        db_session.scalar(select(IngredientAlias).where(IngredientAlias.alias == "atomic alias candidate"))
        is None
    )


@pytest.mark.integration
def test_approve_new_and_proposal_review_commit_atomically(
    client,
    user_headers,
    admin_user,
    catalog_seed,
    db_session: Session,
    monkeypatch,
):
    """New ingredient must not persist if the proposal review update fails."""
    from mealroulette.schemas.ingredient_proposals import IngredientProposalApproveNewRequest
    from mealroulette.services.ingredient_proposals import IngredientProposalService

    created = _create_proposal(client, user_headers, name="Atomic Canonical Root")
    proposal_id = uuid.UUID(created.json()["proposal"]["id"])

    def fail_review(self, *args, **kwargs):
        raise RuntimeError("forced review failure")

    monkeypatch.setattr(IngredientProposalService, "_apply_review", fail_review)
    service = IngredientProposalService(db_session)

    with pytest.raises(RuntimeError, match="forced review failure"):
        service.approve_new(
            proposal_id=proposal_id,
            reviewer=admin_user,
            payload=IngredientProposalApproveNewRequest(
                display_name="Atomic Canonical Root",
                food_group="vegetable",
                family="tomato_family",
            ),
        )

    db_session.rollback()

    proposal = db_session.get(IngredientProposal, proposal_id)
    assert proposal is not None
    assert proposal.resolution_status == "pending"
    assert proposal.resolved_ingredient_id is None
    assert (
        db_session.scalar(
            select(Ingredient).where(Ingredient.canonical_name == "atomic_canonical_root")
        )
        is None
    )