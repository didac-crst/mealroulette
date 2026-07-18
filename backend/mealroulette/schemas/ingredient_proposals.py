from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IngredientProposalSourceTypeValue(str, Enum):
    manual = "manual"
    recipe_editor = "recipe_editor"
    recipe_import = "recipe_import"
    llm_recipe_import = "llm_recipe_import"
    bulk_import = "bulk_import"
    platform_admin = "platform_admin"


class IngredientProposalResolutionStatusValue(str, Enum):
    pending = "pending"
    needs_information = "needs_information"
    duplicate = "duplicate"
    approved = "approved"
    rejected = "rejected"
    withdrawn = "withdrawn"


class IngredientProposalResolutionTypeValue(str, Enum):
    created_canonical = "created_canonical"
    mapped_existing = "mapped_existing"
    added_alias = "added_alias"
    rejected = "rejected"


class IngredientProposalMatchKind(str, Enum):
    ingredient = "ingredient"
    alias = "alias"
    pending_proposal = "pending_proposal"


class IngredientProposalCreateRequest(BaseModel):
    proposed_name: str = Field(min_length=1, max_length=128)
    source_locale: str = Field(min_length=2, max_length=16, default="en")
    description: str | None = Field(default=None, max_length=4000)
    culinary_context: str | None = Field(default=None, max_length=4000)
    suggested_food_group_id: str | None = Field(default=None, max_length=64)
    suggested_family_id: str | None = Field(default=None, max_length=64)
    suggested_storage_class: str | None = Field(default=None, max_length=32)
    suggested_product_form: str | None = Field(default=None, max_length=32)
    suggested_preservation: str | None = Field(default=None, max_length=32)
    source_type: IngredientProposalSourceTypeValue = IngredientProposalSourceTypeValue.manual
    source_reference_type: str | None = Field(default=None, max_length=64)
    source_reference_id: str | None = Field(default=None, max_length=128)


class IngredientProposalProvideInformationRequest(BaseModel):
    description: str | None = Field(default=None, max_length=4000)
    culinary_context: str | None = Field(default=None, max_length=4000)
    review_response: str | None = Field(default=None, max_length=4000)


class IngredientProposalMatchPublic(BaseModel):
    kind: IngredientProposalMatchKind
    label: str
    ingredient_id: int | None = None
    proposal_id: UUID | None = None
    alias: str | None = None


class IngredientProposalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    proposed_name: str
    normalized_name: str
    source_locale: str
    description: str | None
    culinary_context: str | None
    suggested_food_group_id: str | None
    suggested_family_id: str | None
    suggested_storage_class: str | None
    suggested_product_form: str | None
    suggested_preservation: str | None
    resolution_status: IngredientProposalResolutionStatusValue
    resolution_type: IngredientProposalResolutionTypeValue | None
    resolved_ingredient_id: int | None
    proposed_by_user_id: UUID
    household_id: UUID | None
    source_type: IngredientProposalSourceTypeValue
    source_reference_type: str | None
    source_reference_id: str | None
    model_provider: str | None = None
    model_name: str | None = None
    model_confidence: Decimal | None = None
    model_reasoning_summary: str | None = None
    reviewed_by_user_id: UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime
    updated_at: datetime
    suggested_canonical_name: str | None = None


class IngredientProposalCreateResponse(BaseModel):
    proposal: IngredientProposalPublic
    matches: list[IngredientProposalMatchPublic] = Field(default_factory=list)


class IngredientProposalReviewNoteRequest(BaseModel):
    """Required user-facing explanation for reject / request-information."""

    review_note: str = Field(..., min_length=1, max_length=4000)

    @field_validator("review_note")
    @classmethod
    def review_note_must_be_non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("review_note must not be blank")
        return cleaned


class IngredientProposalMapExistingRequest(BaseModel):
    ingredient_id: int
    review_note: str | None = Field(default=None, max_length=4000)


class IngredientProposalAddAliasRequest(BaseModel):
    ingredient_id: int
    alias: str | None = Field(default=None, min_length=1, max_length=128)
    language: str | None = Field(default=None, max_length=16)
    review_note: str | None = Field(default=None, max_length=4000)


class IngredientProposalApproveNewRequest(BaseModel):
    canonical_name: str | None = Field(default=None, min_length=1, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    food_group: str | None = Field(default=None, max_length=64)
    family: str | None = Field(default=None, max_length=64)
    storage_class: str | None = Field(default=None, max_length=32)
    culinary_category: str | None = Field(default=None, max_length=64)
    product_form: str | None = Field(default=None, max_length=32)
    preservation: str | None = Field(default=None, max_length=32)
    default_unit_id: int | None = None
    preferred_shopping_unit_id: int | None = None
    notes: str | None = None
    conversion_notes: str | None = Field(default=None, max_length=4000)
    aliases: list[str] = Field(default_factory=list)
    review_note: str | None = Field(default=None, max_length=4000)


class IngredientProposalMarkDuplicateRequest(BaseModel):
    ingredient_id: int | None = None
    review_note: str = Field(..., min_length=1, max_length=4000)

    @field_validator("review_note")
    @classmethod
    def review_note_must_be_non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("review_note must not be blank")
        return cleaned
