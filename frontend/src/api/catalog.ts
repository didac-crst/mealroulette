import { apiRequest } from "./client";

export type SeasonalityPublic = {
  id: number;
  dish_id: number;
  seasonality_mode: string;
  preferred_months: number[];
  allowed_months: number[];
  excluded_months: number[];
  seasonality_strength: string;
  created_at: string;
  updated_at: string;
};

export type Dish = {
  id: number;
  name: string;
  description: string | null;
  default_servings: number | null;
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  difficulty: string | null;
  active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
  tag_ids: number[];
  seasonality: SeasonalityPublic | null;
};

export type Tag = {
  id: number;
  name: string;
  family: string;
  description: string | null;
};

export type Recipe = {
  id: number;
  dish_id: number;
  variant_name: string;
  description: string | null;
  is_thermomix: boolean;
  servings: number | null;
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  notes: string | null;
};

export type RecipeStep = {
  id: number;
  recipe_id: number;
  step_number: number;
  instruction: string;
  duration_seconds: number | null;
  temperature: string | null;
  timer_seconds: number | null;
  is_thermomix_step: boolean;
};

export type Ingredient = {
  id: number;
  canonical_name: string;
  display_name: string;
  category: string | null;
};

export type RecipeIngredient = {
  id: number;
  recipe_id: number;
  ingredient_id: number;
  quantity: string | null;
  unit_id: number | null;
  optional: boolean;
  notes: string | null;
};

export type Unit = {
  id: number;
  name: string;
  symbol: string;
};

export type DishInput = {
  name: string;
  description?: string | null;
  default_servings?: number | null;
  prep_time_minutes?: number | null;
  cook_time_minutes?: number | null;
  difficulty?: string | null;
  active?: boolean;
  notes?: string | null;
  tag_ids?: number[];
};

export type IngredientResolveResponse = {
  status: "exact" | "suggestions" | "none";
  ingredient?: Ingredient;
  suggestions?: Ingredient[];
};

function withToken(token: string) {
  return { token };
}

export async function fetchDishes(token: string, activeOnly = false): Promise<Dish[]> {
  const query = activeOnly ? "?active_only=true" : "";
  return apiRequest<Dish[]>(`/api/dishes${query}`, withToken(token));
}

export async function fetchDish(token: string, dishId: number): Promise<Dish> {
  return apiRequest<Dish>(`/api/dishes/${dishId}`, withToken(token));
}

export async function createDish(token: string, payload: DishInput): Promise<Dish> {
  return apiRequest<Dish>("/api/dishes", {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function updateDish(token: string, dishId: number, payload: Partial<DishInput>): Promise<Dish> {
  return apiRequest<Dish>(`/api/dishes/${dishId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function deleteDish(token: string, dishId: number): Promise<void> {
  return apiRequest<void>(`/api/dishes/${dishId}`, {
    method: "DELETE",
    ...withToken(token),
  });
}

export async function fetchTags(token: string): Promise<Tag[]> {
  return apiRequest<Tag[]>("/api/tags", withToken(token));
}

export async function fetchRecipes(token: string, dishId: number): Promise<Recipe[]> {
  return apiRequest<Recipe[]>(`/api/dishes/${dishId}/recipes`, withToken(token));
}

export async function createRecipe(
  token: string,
  dishId: number,
  payload: { variant_name: string; description?: string | null },
): Promise<Recipe> {
  return apiRequest<Recipe>(`/api/dishes/${dishId}/recipes`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function fetchRecipeSteps(token: string, recipeId: number): Promise<RecipeStep[]> {
  return apiRequest<RecipeStep[]>(`/api/recipes/${recipeId}/steps`, withToken(token));
}

export async function createRecipeStep(
  token: string,
  recipeId: number,
  payload: { step_number: number; instruction: string },
): Promise<RecipeStep> {
  return apiRequest<RecipeStep>(`/api/recipes/${recipeId}/steps`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function fetchRecipeIngredients(token: string, recipeId: number): Promise<RecipeIngredient[]> {
  return apiRequest<RecipeIngredient[]>(`/api/recipes/${recipeId}/ingredients`, withToken(token));
}

export async function addRecipeIngredient(
  token: string,
  recipeId: number,
  payload: {
    ingredient_id?: number;
    proposed_name?: string;
    quantity?: string | null;
    unit_id?: number | null;
    optional?: boolean;
  },
): Promise<RecipeIngredient> {
  return apiRequest<RecipeIngredient>(`/api/recipes/${recipeId}/ingredients`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function fetchIngredients(token: string): Promise<Ingredient[]> {
  return apiRequest<Ingredient[]>("/api/ingredients", withToken(token));
}

export async function resolveIngredient(token: string, proposedName: string): Promise<IngredientResolveResponse> {
  return apiRequest<IngredientResolveResponse>("/api/ingredients/resolve", {
    method: "POST",
    body: JSON.stringify({ proposed_name: proposedName }),
    ...withToken(token),
  });
}

export async function confirmIngredient(
  token: string,
  payload: {
    action: "create" | "map" | "alias";
    proposed_name: string;
    display_name?: string;
    ingredient_id?: number;
  },
): Promise<Ingredient> {
  return apiRequest<Ingredient>("/api/ingredients/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function fetchUnits(token: string): Promise<Unit[]> {
  return apiRequest<Unit[]>("/api/units", withToken(token));
}
