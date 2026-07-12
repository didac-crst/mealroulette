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
  public_key: string;
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
  computed_traits_json: Record<string, unknown> | null;
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
  public_key: string;
  sequence_number: number;
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
  computed_traits_json: Record<string, unknown> | null;
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
  food_group: string | null;
  family: string | null;
  default_unit_id: number | null;
  default_dimension: "mass" | "volume" | "count" | null;
  preferred_shopping_unit_id: number | null;
  aggregation_unit_id: number | null;
  aggregation_strategy:
    | "strict_same_dimension"
    | "prefer_mass"
    | "prefer_volume"
    | "prefer_count"
    | "allow_approximate_conversion"
    | "never_convert_count"
    | null;
  pantry_item: boolean;
  season_start_month: number | null;
  season_end_month: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type IngredientAlias = {
  id: number;
  ingredient_id: number;
  alias: string;
  language: string | null;
  created_at: string;
  updated_at: string;
};

export type IngredientConversion = {
  id: number;
  ingredient_id: number;
  from_unit_id: number;
  to_unit_id: number;
  from_unit_symbol: string;
  to_unit_symbol: string;
  factor: string;
  confidence: string;
  notes: string | null;
  approved: boolean;
  source: string | null;
  created_at: string;
  updated_at: string;
};

export type IngredientDetail = Ingredient & {
  aliases: IngredientAlias[];
  unit_conversions: IngredientConversion[];
};

export type IngredientInput = {
  canonical_name?: string;
  display_name: string;
  category?: string | null;
  food_group?: string | null;
  family?: string | null;
  default_unit_id?: number | null;
  default_dimension?: Ingredient["default_dimension"];
  preferred_shopping_unit_id?: number | null;
  aggregation_unit_id?: number | null;
  aggregation_strategy?: Ingredient["aggregation_strategy"];
  pantry_item?: boolean;
  season_start_month?: number | null;
  season_end_month?: number | null;
  notes?: string | null;
  aliases?: string[];
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
  dimension: "mass" | "volume" | "count";
};

export type IngredientCategory = {
  id: string;
  label: string;
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

export async function fetchIngredients(token: string, search?: string): Promise<Ingredient[]> {
  const query = search?.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
  return apiRequest<Ingredient[]>(`/api/ingredients${query}`, withToken(token));
}

export async function fetchIngredient(token: string, ingredientId: number): Promise<IngredientDetail> {
  return apiRequest<IngredientDetail>(`/api/ingredients/${ingredientId}`, withToken(token));
}

export async function createIngredient(token: string, payload: IngredientInput): Promise<Ingredient> {
  return apiRequest<Ingredient>("/api/ingredients", {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function updateIngredient(
  token: string,
  ingredientId: number,
  payload: Partial<IngredientInput>,
): Promise<Ingredient> {
  return apiRequest<Ingredient>(`/api/ingredients/${ingredientId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function deleteIngredient(token: string, ingredientId: number): Promise<void> {
  return apiRequest<void>(`/api/ingredients/${ingredientId}`, {
    method: "DELETE",
    ...withToken(token),
  });
}

export async function createIngredientAlias(
  token: string,
  ingredientId: number,
  payload: { alias: string; language?: string | null },
): Promise<IngredientAlias> {
  return apiRequest<IngredientAlias>(`/api/ingredients/${ingredientId}/aliases`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function deleteIngredientAlias(token: string, aliasId: number): Promise<void> {
  return apiRequest<void>(`/api/ingredient-aliases/${aliasId}`, {
    method: "DELETE",
    ...withToken(token),
  });
}

export async function createIngredientConversion(
  token: string,
  ingredientId: number,
  payload: {
    from_unit_id: number;
    to_unit_id: number;
    factor: string;
    confidence?: string;
    notes?: string | null;
    approved?: boolean;
    source?: string;
  },
): Promise<IngredientConversion> {
  return apiRequest<IngredientConversion>(`/api/ingredients/${ingredientId}/conversions`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function updateIngredientConversion(
  token: string,
  conversionId: number,
  payload: {
    factor?: string;
    confidence?: string;
    notes?: string | null;
    approved?: boolean;
    source?: string;
  },
): Promise<IngredientConversion> {
  return apiRequest<IngredientConversion>(`/api/ingredient-conversions/${conversionId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function deleteIngredientConversion(token: string, conversionId: number): Promise<void> {
  return apiRequest<void>(`/api/ingredient-conversions/${conversionId}`, {
    method: "DELETE",
    ...withToken(token),
  });
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

export async function fetchIngredientCategories(token: string): Promise<IngredientCategory[]> {
  return apiRequest<IngredientCategory[]>("/api/ingredient-categories", withToken(token));
}
