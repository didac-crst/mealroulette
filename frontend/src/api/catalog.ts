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
  default_prep_time_minutes: number | null;
  default_cook_time_minutes: number | null;
  default_difficulty: "easy" | "medium" | "hard" | null;
  course: "starter" | "main" | "dessert" | null;
  status: "draft" | "active" | "archived";
  image_url: string | null;
  suitable_for_lunch: boolean | null;
  suitable_for_dinner: boolean | null;
  weekday_friendly: boolean | null;
  leftovers_possible: boolean | null;
  freezer_friendly: boolean | null;
  kids_friendly: boolean | null;
  thermomix_possible: boolean | null;
  active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
  tag_ids: number[];
  seasonality: SeasonalityPublic | null;
};

export type SeasonalityInput = {
  seasonality_mode?: string;
  preferred_months?: number[];
  allowed_months?: number[];
  excluded_months?: number[];
  seasonality_strength?: string;
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
  recipe_type: "standard" | "thermomix" | "other_appliance";
  is_main: boolean;
  is_thermomix: boolean;
  thermomix_model: string | null;
  source_url: string | null;
  servings: number | null;
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  difficulty: "easy" | "medium" | "hard" | null;
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
  image_url?: string | null;
  course?: Dish["course"];
  status?: Dish["status"];
  suitable_for_lunch?: boolean | null;
  suitable_for_dinner?: boolean | null;
  weekday_friendly?: boolean | null;
  leftovers_possible?: boolean | null;
  freezer_friendly?: boolean | null;
  kids_friendly?: boolean | null;
  notes?: string | null;
  tag_ids?: number[];
  seasonality?: SeasonalityInput | null;
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
  payload: {
    variant_name: string;
    description?: string | null;
    recipe_type?: Recipe["recipe_type"];
    is_main?: boolean;
    servings?: number | null;
    prep_time_minutes?: number | null;
    cook_time_minutes?: number | null;
    difficulty?: Recipe["difficulty"];
    source_url?: string | null;
    notes?: string | null;
  },
): Promise<Recipe> {
  return apiRequest<Recipe>(`/api/dishes/${dishId}/recipes`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function updateRecipe(
  token: string,
  recipeId: number,
  payload: {
    variant_name?: string;
    description?: string | null;
    recipe_type?: Recipe["recipe_type"];
    is_main?: boolean;
    servings?: number | null;
    prep_time_minutes?: number | null;
    cook_time_minutes?: number | null;
    difficulty?: Recipe["difficulty"];
    source_url?: string | null;
    notes?: string | null;
  },
): Promise<Recipe> {
  return apiRequest<Recipe>(`/api/recipes/${recipeId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function fetchRecipe(token: string, recipeId: number): Promise<Recipe> {
  return apiRequest<Recipe>(`/api/recipes/${recipeId}`, withToken(token));
}

export async function deleteRecipe(token: string, recipeId: number): Promise<void> {
  return apiRequest<void>(`/api/recipes/${recipeId}`, {
    method: "DELETE",
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

export async function updateRecipeStep(
  token: string,
  stepId: number,
  payload: { step_number?: number; instruction?: string },
): Promise<RecipeStep> {
  return apiRequest<RecipeStep>(`/api/recipe-steps/${stepId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function deleteRecipeStep(token: string, stepId: number): Promise<void> {
  return apiRequest<void>(`/api/recipe-steps/${stepId}`, {
    method: "DELETE",
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

export async function updateRecipeIngredient(
  token: string,
  itemId: number,
  payload: {
    quantity?: string | null;
    unit_id?: number | null;
    optional?: boolean;
    notes?: string | null;
  },
): Promise<RecipeIngredient> {
  return apiRequest<RecipeIngredient>(`/api/recipe-ingredients/${itemId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function deleteRecipeIngredient(token: string, itemId: number): Promise<void> {
  return apiRequest<void>(`/api/recipe-ingredients/${itemId}`, {
    method: "DELETE",
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
