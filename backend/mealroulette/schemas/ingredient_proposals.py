from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


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


def _require_trimmed_nonblank(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be blank")
    return cleaned


def _trim_optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    cleaned = value.strip()
    return cleaned or None


class IngredientProposalCreateRequest(BaseModel):
    """Member create payload. Provenance is always derived server-side as manual."""

    proposed_name: str = Field(min_length=1, max_length=128)
    source_locale: str = Field(min_length=2, max_length=16, default="en")
    description: str | None = Field(default=None, max_length=4000)
    culinary_context: str | None = Field(default=None, max_length=4000)
    suggested_food_group_id: str | None = Field(default=None, max_length=64)
    suggested_family_id: str | None = Field(default=None, max_length=64)
    suggested_storage_class: str | None = Field(default=None, max_length=32)
    suggested_product_form: str | None = Field(default=None, max_length=32)
    suggested_preservation: str | None = Field(default=None, max_length=32)

    @field_validator("proposed_name", "source_locale", mode="before")
    @classmethod
    def trim_required_text(cls, value: object, info: ValidationInfo) -> str:
        return _require_trimmed_nonblank(value, field_name=info.field_name)


class IngredientProposalProvideInformationRequest(BaseModel):
    description: str | None = Field(default=None, max_length=4000)
    culinary_context: str | None = Field(default=None, max_length=4000)
    review_response: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def require_meaningful_update(self) -> IngredientProposalProvideInformationRequest:
        values = (self.description, self.culinary_context, self.review_response)
        if all(value is None for value in values):
            raise ValueError(
                "Provide at least one of description, culinary_context, or review_response"
            )
        if not any(value is not None and bool(value.strip()) for value in values):
            raise ValueError(
                "Provide at least one non-blank description, culinary_context, or review_response"
            )
        return self


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

    @field_validator("review_note", mode="before")
    @classmethod
    def review_note_must_be_non_blank(cls, value: object) -> str:
        return _require_trimmed_nonblank(value, field_name="review_note")


class IngredientProposalMapExistingRequest(BaseModel):
    ingredient_id: int
    review_note: str | None = Field(default=None, max_length=4000)


class IngredientProposalAddAliasRequest(BaseModel):
    ingredient_id: int
    alias: str | None = Field(default=None, min_length=1, max_length=128)
    language: str | None = Field(default=None, max_length=16)
    review_note: str | None = Field(default=None, max_length=4000)

    @field_validator("alias", mode="before")
    @classmethod
    def trim_alias(cls, value: object) -> str | None:
        if value is None:
            return None
        return _require_trimmed_nonblank(value, field_name="alias")

    @field_validator("language", mode="before")
    @classmethod
    def trim_language(cls, value: object) -> str | None:
        return _trim_optional_text(value)


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

    @field_validator("canonical_name", "display_name", mode="before")
    @classmethod
    def trim_optional_names(cls, value: object, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        return _require_trimmed_nonblank(value, field_name=info.field_name)


class IngredientProposalMarkDuplicateRequest(BaseModel):
    ingredient_id: int | None = None
    review_note: str = Field(..., min_length=1, max_length=4000)

    @field_validator("review_note", mode="before")
    @classmethod
    def review_note_must_be_non_blank(cls, value: object) -> str:
        return _require_trimmed_nonblank(value, field_name="review_note")
