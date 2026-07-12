import type { Dish } from "../../api/catalog";

export function normalizeDishSearchQuery(query: string): string {
  return query.trim().toLowerCase();
}

export function dishSearchTokens(query: string): string[] {
  return normalizeDishSearchQuery(query).split(/\s+/).filter(Boolean);
}

export function dishSearchHaystack(dish: Dish, recipeVariantNames: string[] = []): string {
  return [dish.name, dish.description ?? "", ...recipeVariantNames].join(" ").toLowerCase();
}

export function dishMatchesSearch(
  dish: Dish,
  query: string,
  recipeVariantNames: string[] = [],
): boolean {
  const tokens = dishSearchTokens(query);
  if (tokens.length === 0) {
    return true;
  }
  const haystack = dishSearchHaystack(dish, recipeVariantNames);
  return tokens.every((token) => haystack.includes(token));
}

export function filterDishesBySearch(
  dishes: Dish[],
  query: string,
  recipeNamesByDishId: Record<number, string[]> = {},
): Dish[] {
  const tokens = dishSearchTokens(query);
  if (tokens.length === 0) {
    return dishes;
  }
  return dishes.filter((dish) => dishMatchesSearch(dish, query, recipeNamesByDishId[dish.id] ?? []));
}
