import type { Dish } from "../../api/catalog";
import type { MealPlanDishLineRole, MealPlanItem } from "../../api/planning";

export type MealLineRoleFilter = "all" | "main" | "centerpiece" | "side" | "dessert";

const FILTER_OPTIONS: MealLineRoleFilter[] = ["all", "main", "centerpiece", "side", "dessert"];

export function mealLineRoleFilterLabel(filter: MealLineRoleFilter): string {
  switch (filter) {
    case "all":
      return "All";
    case "main":
      return "Main";
    case "centerpiece":
      return "Centerpiece";
    case "side":
      return "Side";
    case "dessert":
      return "Dessert";
  }
}

export function mealLineRoleFilterOptions(): MealLineRoleFilter[] {
  return FILTER_OPTIONS;
}

export function filterDishesByMealLineRole(dishes: Dish[], filter: MealLineRoleFilter): Dish[] {
  if (filter === "all") {
    return dishes;
  }
  return dishes.filter((dish) => {
    switch (filter) {
      case "main":
        return dish.meal_composition === "main_dish";
      case "centerpiece":
        return dish.meal_composition === "simple_dish" && dish.simple_dish_part === "centerpiece";
      case "side":
        return dish.meal_composition === "simple_dish" && dish.simple_dish_part === "sidedish";
      case "dessert":
        return dish.meal_composition === "dessert";
      default:
        return true;
    }
  });
}

export function suggestedMealLineRoleFilter(item: MealPlanItem): MealLineRoleFilter {
  const lines = item.lines ?? [];
  if (lines.length === 0) {
    return "all";
  }
  const roles = new Set(lines.map((line) => line.role));
  if (roles.has("centerpiece") && !roles.has("side")) {
    return "side";
  }
  if (roles.has("side") && !roles.has("centerpiece") && !roles.has("main")) {
    return "centerpiece";
  }
  if (roles.has("main")) {
    return "side";
  }
  return "all";
}

export function formatMealLineRole(role: MealPlanDishLineRole): string {
  switch (role) {
    case "main":
      return "Main";
    case "centerpiece":
      return "Centerpiece";
    case "side":
      return "Side";
    case "dessert":
      return "Dessert";
    case "extra":
      return "Extra";
  }
}

export function formatMealLineSource(source: "roulette" | "manual" | "leftover"): string {
  switch (source) {
    case "roulette":
      return "Roulette";
    case "manual":
      return "Manual";
    case "leftover":
      return "Leftover";
  }
}
