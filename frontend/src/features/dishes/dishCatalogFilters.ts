import type { Dish } from "../../api/catalog";

/** Browse filters aligned with planner meal roles (not legacy dish.course alone). */
export type DishCatalogFilter = "all" | "main_dish" | "centerpiece" | "sidedish" | "dessert";

export const DISH_CATALOG_FILTERS: DishCatalogFilter[] = [
  "all",
  "main_dish",
  "centerpiece",
  "sidedish",
  "dessert",
];

const FILTER_LABELS: Record<DishCatalogFilter, string> = {
  all: "All",
  main_dish: "Main dishes",
  centerpiece: "Centerpieces",
  sidedish: "Side dishes",
  dessert: "Desserts",
};

export function dishMatchesCatalogFilter(dish: Dish, filter: DishCatalogFilter): boolean {
  if (filter === "all") {
    return true;
  }
  if (filter === "main_dish") {
    return dish.meal_composition === "main_dish";
  }
  if (filter === "dessert") {
    return dish.meal_composition === "dessert" || dish.course === "dessert";
  }
  if (filter === "centerpiece") {
    return dish.simple_dish_part === "centerpiece";
  }
  if (filter === "sidedish") {
    return dish.simple_dish_part === "sidedish";
  }
  return false;
}

export function filterDishesByCatalog(dishes: Dish[], filter: DishCatalogFilter): Dish[] {
  if (filter === "all") {
    return dishes;
  }
  return dishes.filter((dish) => dishMatchesCatalogFilter(dish, filter));
}

/** Always offer All + planner-role chips so users can browse by composition. */
export function availableCatalogFilters(_dishes?: Dish[]): DishCatalogFilter[] {
  return [...DISH_CATALOG_FILTERS];
}

export function catalogFilterLabel(filter: DishCatalogFilter): string {
  return FILTER_LABELS[filter];
}
