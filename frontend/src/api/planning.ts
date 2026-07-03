import { apiRequest } from "./client";

export type MealSlot = "lunch" | "dinner";
export type MealPlanItemStatus = "planned" | "eaten" | "skipped" | "ate_leftovers";

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
  is_locked: boolean;
  manually_selected: boolean;
  skip_reason: string | null;
  skip_comment: string | null;
  leftover_source_item_id: number | null;
  selection_reasons_json: Record<string, unknown> | null;
  review_saved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type MealPlan = {
  id: number;
  week_start_date: string;
  status: "draft" | "active" | "archived";
  items: MealPlanItem[];
  created_at: string;
  updated_at: string;
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
