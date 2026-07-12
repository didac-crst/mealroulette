from pydantic import BaseModel, Field


class FoodGroupPublic(BaseModel):
    id: str
    label: str
    description: str


class IngredientFamilyPublic(BaseModel):
    id: str
    food_group: str
    label: str
    description: str


class IngredientTaxonomySummary(BaseModel):
    id: int
    canonical_name: str
    display_name: str
    food_group: str | None
    family: str | None
    pantry_item: bool
    alias_count: int
    approved_conversion_count: int
    unapproved_conversion_count: int
    missing_family: bool
    missing_food_group: bool


class FoodGroupOverview(BaseModel):
    id: str
    label: str
    family_count: int
    ingredient_count: int
    missing_metadata_count: int


class IngredientTaxonomyOverview(BaseModel):
    totals: dict[str, int]
    food_groups: list[FoodGroupOverview]


class IngredientResolveMatch(BaseModel):
    canonical_name: str
    display_name: str
    food_group: str | None
    family: str | None
    score: float | None = None


class IngredientResolveResponseV2(BaseModel):
    status: str
    query: str
    matched_on: str | None = None
    matched_value: str | None = None
    ingredient: IngredientResolveMatch | None = None
    suggestions: list[IngredientResolveMatch] = Field(default_factory=list)


class ClassifyCandidateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    context: str | None = Field(default=None, max_length=1024)
    language: str | None = Field(default=None, max_length=16)


class ClassifySuggestion(BaseModel):
    id: str
    reason: str
    food_group: str | None = None


class ClassifyIngredientSuggestion(BaseModel):
    canonical_name: str
    display_name: str
    family: str | None
    food_group: str | None
    reason: str
    score: float | None = None


class ClassifyCandidateResponse(BaseModel):
    status: str
    query: str
    food_groups: list[ClassifySuggestion] = Field(default_factory=list)
    families: list[ClassifySuggestion] = Field(default_factory=list)
    ingredients: list[ClassifyIngredientSuggestion] = Field(default_factory=list)
    draft: dict | None = None
