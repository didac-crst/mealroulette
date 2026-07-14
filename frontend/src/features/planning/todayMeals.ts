import type { Recipe } from "../../api/catalog";
import type { MealPlanDishLine, MealPlanItem } from "../../api/planning";
import { formatMealLineRole } from "./mealLineFilters";
import { hasMealAssignment, sortedMealLines } from "./planFormat";

export type CookOption = {
  key: string;
  dishId: number;
  dishName: string;
  recipeId: number;
  roleLabel: string;
};

export function resolveCookRecipeId(item: MealPlanItem, recipes: Recipe[]): number | null {
  if (item.recipe_id != null) {
    return item.recipe_id;
  }
  const main = recipes.find((recipe) => recipe.is_main);
  if (main) {
    return main.id;
  }
  return recipes[0]?.id ?? null;
}

export function resolveLineCookRecipeId(line: MealPlanDishLine, recipes: Recipe[]): number | null {
  if (line.recipe_id != null) {
    return line.recipe_id;
  }
  const main = recipes.find((recipe) => recipe.is_main);
  if (main) {
    return main.id;
  }
  return recipes[0]?.id ?? null;
}

export function cookableDishIds(item: MealPlanItem): number[] {
  const lineIds = sortedMealLines(item)
    .map((line) => line.dish_id)
    .filter((dishId): dishId is number => dishId != null);
  if (lineIds.length > 0) {
    return [...new Set(lineIds)];
  }
  return item.dish_id != null ? [item.dish_id] : [];
}

export function buildCookOptions(
  item: MealPlanItem,
  recipesByDishId: Map<number, Recipe[]>,
): CookOption[] {
  const lines = sortedMealLines(item).filter((line) => line.dish_id != null);
  const sourceLines =
    lines.length > 0
      ? lines
      : item.dish_id != null
        ? [
            {
              id: item.id,
              dish_id: item.dish_id,
              dish_name: item.dish_name,
              recipe_id: item.recipe_id,
              role: "main" as const,
            } as MealPlanDishLine,
          ]
        : [];

  const options: CookOption[] = [];
  for (const line of sourceLines) {
    if (line.dish_id == null) {
      continue;
    }
    const recipes = recipesByDishId.get(line.dish_id) ?? [];
    const recipeId = resolveLineCookRecipeId(line, recipes);
    if (recipeId == null) {
      continue;
    }
    options.push({
      key: `${line.role}-${line.dish_id}-${recipeId}`,
      dishId: line.dish_id,
      dishName: line.dish_name ?? item.dish_name ?? "Dish",
      recipeId,
      roleLabel: formatMealLineRole(line.role),
    });
  }
  return options;
}

export function canOpenCookMode(item: MealPlanItem): boolean {
  return hasMealAssignment(item) && item.status !== "ate_leftovers";
}
