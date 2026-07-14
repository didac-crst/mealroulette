import { apiRequest } from "./client";

export type MealSlot = "lunch" | "dinner";
export type MealPlanItemStatus = "planned" | "eaten" | "skipped" | "ate_leftovers";
export type MealPlanningState = "open" | "do_not_plan";
export type MealPlanDishLineRole = "main" | "centerpiece" | "side" | "dessert" | "extra";
export type MealPlanDishLineSource = "roulette" | "manual" | "leftover";
export type MealPlanAssignMode = "add" | "replace_roulette" | "replace_all";

export type MealPlanDishLine = {
  id: number;
  meal_plan_item_id: number;
  dish_id: number | null;
  recipe_id: number | null;
  dish_name: string | null;
  recipe_variant_name: string | null;
  role: MealPlanDishLineRole;
  source: MealPlanDishLineSource;
  position: number;
  selection_reasons_json: Record<string, unknown> | null;
  computed_traits_json: Record<string, unknown> | null;
};

export type MealPlanItem = {
  id: number;
  meal_plan_id: number;
  date: string;
  meal_slot: MealSlot;
  dish_id: number | null;
  recipe_id: number | null;
  dish_name: string | null;
  recipe_variant_name: string | null;
  status: MealPlanItemStatus;
  planning_state: MealPlanningState;
  title: string;
  lines: MealPlanDishLine[];
  is_locked: boolean;
  manually_selected: boolean;
  skip_reason: string | null;
  skip_comment: string | null;
  leftover_source_item_id: number | null;
  selection_reasons_json: Record<string, unknown> | null;
  computed_traits_json: Record<string, unknown> | null;
  review_saved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type MealPlan = {
  id: number;
  week_start_date: string;
  status: "draft" | "active" | "archived";
  items: MealPlanItem[];
  roulette_undo_available: boolean;
  created_at: string;
  updated_at: string;
};

export type MealPlanRouletteResponse = {
  warnings: string[];
  variety: {
    average_distance_to_neighbours: number | null;
    items: Array<{
      dish_id: number;
      dish_name: string;
      nearest_neighbour_dish: string | null;
      nearest_neighbour_date?: string;
      distance: number | null;
      variety_label: string;
    }>;
  };
  assignments_count: number;
  total_score: number;
  can_undo: boolean;
};

export type MealPlanUndoRouletteResponse = {
  restored: boolean;
  can_undo: boolean;
};

export type MealPlanItemSwapResponse = {
  source: MealPlanItem;
  target: MealPlanItem;
};

export type MealRating = {
  id: number;
  meal_plan_item_id: number;
  dish_id: number;
  recipe_id: number | null;
  rating: number;
  comment: string | null;
  created_at: string;
};

export async function fetchCurrentMealPlan(token: string): Promise<MealPlan> {
  return apiRequest<MealPlan>("/api/meal-plans/current", { token });
}

export async function fetchMealPlanByWeek(token: string, weekStart: string): Promise<MealPlan> {
  return apiRequest<MealPlan>(`/api/meal-plans/${weekStart}`, { token });
}

export async function updateMealPlanItem(
  token: string,
  itemId: number,
  body: {
    dish_id?: number | null;
    recipe_id?: number | null;
    status?: MealPlanItemStatus;
    is_locked?: boolean;
    skip_reason?: string | null;
    skip_comment?: string | null;
    leftover_source_item_id?: number | null;
  },
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(body),
  });
}

export async function markMealPlanItemEaten(token: string, itemId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/mark-eaten`, {
    method: "POST",
    token,
  });
}

export async function skipMealPlanItem(
  token: string,
  itemId: number,
  skipReason?: string,
  skipComment?: string,
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/skip`, {
    method: "POST",
    token,
    body: JSON.stringify({
      ...(skipReason ? { skip_reason: skipReason } : {}),
      ...(skipComment ? { skip_comment: skipComment } : {}),
    }),
  });
}

export async function markMealPlanItemAteLeftovers(
  token: string,
  itemId: number,
  leftoverSourceItemId?: number,
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/ate-leftovers`, {
    method: "POST",
    token,
    body: JSON.stringify(
      leftoverSourceItemId ? { leftover_source_item_id: leftoverSourceItemId } : {},
    ),
  });
}

export async function lockMealPlanItem(token: string, itemId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/lock`, {
    method: "POST",
    token,
  });
}

export async function unlockMealPlanItem(token: string, itemId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/unlock`, {
    method: "POST",
    token,
  });
}

export async function resetMealPlanItemStatus(token: string, itemId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/reset-status`, {
    method: "POST",
    token,
  });
}

export async function fetchMealHistory(token: string, limit = 20): Promise<MealPlanItem[]> {
  return apiRequest<MealPlanItem[]>(`/api/meal-history?limit=${limit}`, { token });
}

export async function fetchMealRating(token: string, itemId: number): Promise<MealRating | null> {
  return apiRequest<MealRating | null>(`/api/meal-plan-items/${itemId}/rating`, { token });
}

export type MealRatingUpsertResponse = {
  rating: MealRating;
  item: MealPlanItem;
};

export async function upsertMealRating(
  token: string,
  itemId: number,
  body: { rating: number; comment?: string | null },
): Promise<MealRatingUpsertResponse> {
  return apiRequest<MealRatingUpsertResponse>(`/api/meal-plan-items/${itemId}/rating`, {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function generateMealPlanWeek(token: string, mealPlanId: number): Promise<MealPlan> {
  return apiRequest<MealPlan>(`/api/meal-plans/${mealPlanId}/generate`, {
    method: "POST",
    token,
  });
}

export async function generateMealPlanWeekDetails(
  token: string,
  mealPlanId: number,
): Promise<MealPlanRouletteResponse> {
  return apiRequest<MealPlanRouletteResponse>(`/api/meal-plans/${mealPlanId}/generate/details`, {
    method: "POST",
    token,
    timeoutMs: 60_000,
  });
}

export async function rerollMealPlanItem(token: string, itemId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/reroll`, {
    method: "POST",
    token,
  });
}

export async function undoMealPlanRoulette(token: string, mealPlanId: number): Promise<MealPlanUndoRouletteResponse> {
  return apiRequest<MealPlanUndoRouletteResponse>(`/api/meal-plans/${mealPlanId}/undo-roulette`, {
    method: "POST",
    token,
  });
}

export async function swapMealPlanItems(
  token: string,
  sourceItemId: number,
  targetItemId: number,
): Promise<MealPlanItemSwapResponse> {
  return apiRequest<MealPlanItemSwapResponse>(`/api/meal-plan-items/${sourceItemId}/swap`, {
    method: "POST",
    token,
    body: JSON.stringify({ target_item_id: targetItemId }),
  });
}

export async function assignMealPlanSlot(
  token: string,
  body: {
    date: string;
    meal_slot: MealSlot;
    dish_id: number;
    recipe_id?: number | null;
    mode?: MealPlanAssignMode;
  },
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>("/api/meal-plan-items/assign", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function addMealPlanLine(
  token: string,
  itemId: number,
  body: {
    dish_id: number;
    recipe_id?: number | null;
    role?: MealPlanDishLineRole;
    position?: number;
  },
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/lines`, {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function updateMealPlanLine(
  token: string,
  lineId: number,
  body: {
    dish_id?: number;
    recipe_id?: number | null;
    role?: MealPlanDishLineRole;
    position?: number;
  },
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-item-lines/${lineId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(body),
  });
}

export async function deleteMealPlanLine(token: string, lineId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-item-lines/${lineId}`, {
    method: "DELETE",
    token,
  });
}

export async function markMealDoNotPlan(
  token: string,
  itemId: number,
  removeExistingLines = true,
): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/do-not-plan`, {
    method: "POST",
    token,
    body: JSON.stringify({ remove_existing_lines: removeExistingLines }),
  });
}

export async function reopenMealSlot(token: string, itemId: number): Promise<MealPlanItem> {
  return apiRequest<MealPlanItem>(`/api/meal-plan-items/${itemId}/reopen`, {
    method: "POST",
    token,
  });
}
