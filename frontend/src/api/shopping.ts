import { apiRequest } from "./client";

export type ShoppingQuantityComponent = {
  quantity: string;
  unit_symbol: string;
};

export type ShoppingSourceContribution = {
  meal_plan_item_id: number;
  date: string;
  meal_slot: "lunch" | "dinner";
  dish_name: string;
  recipe_variant_name: string | null;
  quantity: string;
  unit_symbol: string;
  optional: boolean;
};

export type ShoppingPlannedMeal = {
  meal_plan_item_id: number;
  date: string;
  meal_slot: "lunch" | "dinner";
  dish_name: string;
  recipe_variant_name: string | null;
};

export type ShoppingListItem = {
  id: number | null;
  ingredient_id: number;
  display_name: string;
  quantity: string;
  unit_id: number;
  unit_symbol: string;
  category: string;
  checked: boolean;
  approximate: boolean;
  optional: boolean;
  source_meal_plan_item_ids: number[];
  source_contributions: ShoppingSourceContribution[];
  raw_components: ShoppingQuantityComponent[];
};

export type ShoppingList = {
  id: number | null;
  from_date: string;
  to_date: string;
  status: "draft" | "active" | "completed" | "archived";
  exclude_pantry: boolean;
  items: ShoppingListItem[];
  planned_meals: ShoppingPlannedMeal[];
};

export async function previewShoppingList(
  token: string,
  params: { from: string; days: number; exclude_pantry: boolean },
): Promise<ShoppingList> {
  const search = new URLSearchParams({
    from: params.from,
    days: String(params.days),
    exclude_pantry: String(params.exclude_pantry),
  });
  return apiRequest<ShoppingList>(`/api/shopping-list?${search.toString()}`, { token });
}

export async function createShoppingList(
  token: string,
  body: { from_date: string; days: number; exclude_pantry: boolean },
): Promise<ShoppingList> {
  return apiRequest<ShoppingList>("/api/shopping-lists", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function fetchShoppingList(token: string, shoppingListId: number): Promise<ShoppingList> {
  return apiRequest<ShoppingList>(`/api/shopping-lists/${shoppingListId}`, { token });
}

export async function updateShoppingListItem(
  token: string,
  itemId: number,
  body: { checked: boolean },
): Promise<ShoppingListItem> {
  return apiRequest<ShoppingListItem>(`/api/shopping-list-items/${itemId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(body),
  });
}
