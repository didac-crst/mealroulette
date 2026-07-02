import type { Recipe } from "../../api/catalog";
import { formatDifficulty } from "./constants";

export function formatRecipeDifficulty(recipe: Pick<Recipe, "difficulty">): string {
  return formatDifficulty(recipe.difficulty);
}

export function formatRecipeTime(recipe: Pick<Recipe, "prep_time_minutes" | "cook_time_minutes">): string {
  const prep = recipe.prep_time_minutes;
  const cook = recipe.cook_time_minutes;
  return `${prep ?? "—"} / ${cook ?? "—"} min`;
}
