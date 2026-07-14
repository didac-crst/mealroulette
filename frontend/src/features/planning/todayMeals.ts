import type { Recipe } from "../../api/catalog";
import type { MealPlanItem } from "../../api/planning";
import { hasMealAssignment } from "./planFormat";

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

export function canOpenCookMode(item: MealPlanItem): boolean {
  return hasMealAssignment(item) && item.status !== "ate_leftovers";
}
