import { apiRequest } from "./client";

export type FoodGroup = {
  id: string;
  label: string;
  description: string;
};

export type IngredientFamily = {
  id: string;
  food_group: string;
  label: string;
  description: string;
};

export type IngredientTaxonomySummary = {
  id: number;
  canonical_name: string;
  display_name: string;
  food_group: string | null;
  family: string | null;
  pantry_item: boolean;
  alias_count: number;
  approved_conversion_count: number;
  unapproved_conversion_count: number;
  missing_family: boolean;
  missing_food_group: boolean;
};

export type IngredientTaxonomyOverview = {
  totals: Record<string, number>;
  food_groups: Array<{
    id: string;
    label: string;
    family_count: number;
    ingredient_count: number;
    missing_metadata_count: number;
  }>;
};

export type IngredientResolveMatch = {
  canonical_name: string;
  display_name: string;
  food_group: string | null;
  family: string | null;
  score: number | null;
};

export type IngredientResolveV2Response = {
  status: string;
  query: string;
  matched_on?: string | null;
  matched_value?: string | null;
  ingredient?: IngredientResolveMatch | null;
  suggestions?: IngredientResolveMatch[];
};

export type ClassifyCandidateResponse = {
  status: string;
  query: string;
  food_groups: Array<{ id: string; reason: string; food_group?: string | null }>;
  families: Array<{ id: string; reason: string; food_group?: string | null }>;
  ingredients: Array<{
    canonical_name: string;
    display_name: string;
    family: string | null;
    food_group: string | null;
    reason: string;
    score: number | null;
  }>;
  draft: Record<string, unknown> | null;
};

export function fetchFoodGroups(token: string): Promise<FoodGroup[]> {
  return apiRequest<FoodGroup[]>("/api/food-groups", { token });
}

export function fetchFoodGroupFamilies(token: string, foodGroupId: string): Promise<IngredientFamily[]> {
  return apiRequest<IngredientFamily[]>(`/api/food-groups/${encodeURIComponent(foodGroupId)}/families`, { token });
}

export function fetchFamilyIngredients(token: string, familyId: string): Promise<IngredientTaxonomySummary[]> {
  return apiRequest<IngredientTaxonomySummary[]>(
    `/api/ingredient-families/${encodeURIComponent(familyId)}/ingredients`,
    { token },
  );
}

export function fetchIngredientTaxonomyOverview(token: string): Promise<IngredientTaxonomyOverview> {
  return apiRequest<IngredientTaxonomyOverview>("/api/ingredient-taxonomy/overview", { token });
}

export function resolveIngredientV2(token: string, proposedName: string): Promise<IngredientResolveV2Response> {
  return apiRequest<IngredientResolveV2Response>("/api/ingredients/resolve-v2", {
    method: "POST",
    token,
    body: JSON.stringify({ proposed_name: proposedName }),
  });
}

export function classifyIngredientCandidate(
  token: string,
  payload: { name: string; context?: string; language?: string },
): Promise<ClassifyCandidateResponse> {
  return apiRequest<ClassifyCandidateResponse>("/api/ingredients/classify-candidate", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}
