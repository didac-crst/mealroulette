import { apiRequest } from "./client";

export type PublicRecipeStatus =
  | "submitted"
  | "public"
  | "rejected"
  | "withdrawn"
  | "delisted";

export type PublicRecipeVersion = {
  id: string;
  version_number: number;
  published_at: string | null;
  superseded_at: string | null;
  created_at: string;
};

export type PublicRecipeMember = {
  id: string;
  status: PublicRecipeStatus;
  title: string;
  description: string | null;
  current_version: PublicRecipeVersion;
  snapshot: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type PublicRecipeHousehold = {
  id: string;
  status: PublicRecipeStatus;
  originating_dish_id: number;
  originating_recipe_id: number;
  current_version_id: string | null;
  title: string;
  description: string | null;
  review_note: string | null;
  reviewed_at: string | null;
  latest_version: PublicRecipeVersion | null;
  created_at: string;
  updated_at: string;
};

export type PublicRecipePlatform = {
  id: string;
  status: PublicRecipeStatus;
  originating_household_id: string;
  originating_dish_id: number;
  originating_recipe_id: number;
  current_version_id: string | null;
  submitted_by_user_id: string;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  title: string;
  description: string | null;
  latest_version: PublicRecipeVersion | null;
  current_version: PublicRecipeVersion | null;
  snapshot: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type PublicRecipeAdoptResult = {
  dish_id: number;
  recipe_id: number;
  dish_public_key: string;
  recipe_public_key: string;
  derived_from_public_recipe_id: string;
  derived_from_public_version_id: string;
};

export function listPublicRecipes(token: string) {
  return apiRequest<PublicRecipeMember[]>("/api/public-recipes", { token });
}

export function getPublicRecipe(token: string, publicRecipeId: string) {
  return apiRequest<PublicRecipeMember>(`/api/public-recipes/${publicRecipeId}`, { token });
}

export function adoptPublicRecipe(token: string, publicRecipeId: string) {
  return apiRequest<PublicRecipeAdoptResult>(`/api/public-recipes/${publicRecipeId}/adopt`, {
    method: "POST",
    token,
  });
}

export function submitPublishRequest(token: string, recipeId: number) {
  return apiRequest<PublicRecipeHousehold>(`/api/recipes/${recipeId}/publish-request`, {
    method: "POST",
    token,
  });
}

export function listHouseholdPublicationRequests(token: string) {
  return apiRequest<PublicRecipeHousehold[]>("/api/household/publication-requests", { token });
}

export function withdrawPublicationRequest(token: string, publicRecipeId: string) {
  return apiRequest<PublicRecipeHousehold>(
    `/api/household/publication-requests/${publicRecipeId}/withdraw`,
    { method: "POST", token },
  );
}

export function listPlatformPublicRecipes(token: string, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest<PublicRecipePlatform[]>(`/api/platform/public-recipes${query}`, { token });
}

export function getPlatformPublicRecipe(token: string, publicRecipeId: string) {
  return apiRequest<PublicRecipePlatform>(`/api/platform/public-recipes/${publicRecipeId}`, {
    token,
  });
}

export function approvePublicRecipe(token: string, publicRecipeId: string, reviewNote?: string) {
  return apiRequest<PublicRecipePlatform>(`/api/platform/public-recipes/${publicRecipeId}/approve`, {
    method: "POST",
    token,
    body: JSON.stringify({ review_note: reviewNote ?? null }),
  });
}

export function rejectPublicRecipe(token: string, publicRecipeId: string, reviewNote: string) {
  return apiRequest<PublicRecipePlatform>(`/api/platform/public-recipes/${publicRecipeId}/reject`, {
    method: "POST",
    token,
    body: JSON.stringify({ review_note: reviewNote }),
  });
}

export function delistPublicRecipe(token: string, publicRecipeId: string, reviewNote: string) {
  return apiRequest<PublicRecipePlatform>(`/api/platform/public-recipes/${publicRecipeId}/delist`, {
    method: "POST",
    token,
    body: JSON.stringify({ review_note: reviewNote }),
  });
}
