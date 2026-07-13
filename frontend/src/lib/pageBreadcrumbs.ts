export type BreadcrumbItem = {
  label: string;
  to?: string;
};

export type BreadcrumbLabels = {
  dishId?: number | null;
  dishName?: string | null;
  recipeId?: number | null;
  recipeName?: string | null;
  ingredientId?: number | null;
  ingredientName?: string | null;
};

type RouteParams = {
  dishId?: string;
  recipeId?: string;
  ingredientId?: string;
};

function dishCrumb(labels: BreadcrumbLabels, dishId?: string): BreadcrumbItem {
  const id = labels.dishId ?? (dishId ? Number(dishId) : null);
  const label = labels.dishName?.trim() || "Dish";
  return id ? { label, to: `/dishes/${id}` } : { label };
}

function ingredientCrumb(labels: BreadcrumbLabels, ingredientId?: string): BreadcrumbItem {
  const id = labels.ingredientId ?? (ingredientId ? Number(ingredientId) : null);
  const label = labels.ingredientName?.trim() || "Ingredient";
  return id ? { label, to: `/ingredients/${id}` } : { label };
}

export function resolveBreadcrumbs(
  pathname: string,
  params: RouteParams = {},
  labels: BreadcrumbLabels = {},
): BreadcrumbItem[] {
  const dishes = { label: "Dishes", to: "/dishes" };
  const settings = { label: "Settings", to: "/settings" };
  const ingredients = { label: "Ingredients", to: "/ingredients" };

  if (pathname === "/today") {
    return [{ label: "Today" }];
  }
  if (pathname === "/plan") {
    return [{ label: "Plan" }];
  }
  if (pathname === "/review") {
    return [{ label: "Review" }];
  }
  if (pathname === "/shopping") {
    return [{ label: "Shopping" }];
  }
  if (pathname === "/dishes") {
    return [dishes];
  }
  if (pathname === "/dishes/new") {
    return [dishes, { label: "New dish" }];
  }
  if (pathname === `/dishes/${params.dishId}/edit`) {
    return [dishes, dishCrumb(labels, params.dishId), { label: "Edit" }];
  }
  if (pathname === `/dishes/${params.dishId}/recipes/new`) {
    return [dishes, dishCrumb(labels, params.dishId), { label: "New recipe" }];
  }
  if (pathname === `/dishes/${params.dishId}/recipes/${params.recipeId}/edit`) {
    const recipeLabel = labels.recipeName?.trim() || "Recipe";
    const recipeId = labels.recipeId ?? (params.recipeId ? Number(params.recipeId) : null);
    const recipeCrumb: BreadcrumbItem = recipeId
      ? { label: recipeLabel, to: `/dishes/${params.dishId}/recipes/${recipeId}` }
      : { label: recipeLabel };
    return [dishes, dishCrumb(labels, params.dishId), recipeCrumb, { label: "Edit" }];
  }
  if (pathname === `/dishes/${params.dishId}/recipes/${params.recipeId}`) {
    return [dishes, dishCrumb(labels, params.dishId), { label: labels.recipeName?.trim() || "Recipe" }];
  }
  if (pathname === `/dishes/${params.dishId}`) {
    return [dishes, { label: labels.dishName?.trim() || "Dish" }];
  }
  if (pathname === `/recipes/${params.recipeId}/cook`) {
    return [dishes, dishCrumb(labels), { label: "Cook" }];
  }

  if (pathname === "/settings") {
    return [settings];
  }
  if (pathname === "/settings/targets") {
    return [settings, { label: "Weekly targets" }];
  }
  if (pathname === "/settings/scheduler") {
    return [settings, { label: "Auto roulette" }];
  }
  if (pathname === "/settings/telegram") {
    return [settings, { label: "Telegram" }];
  }
  if (pathname === "/settings/backups") {
    return [settings, { label: "Backups" }];
  }

  if (pathname === "/ingredients") {
    return [settings, ingredients];
  }
  if (pathname === "/ingredients/taxonomy") {
    return [settings, ingredients, { label: "Taxonomy" }];
  }
  if (pathname === "/ingredients/new") {
    return [settings, ingredients, { label: "New ingredient" }];
  }
  if (pathname === `/ingredients/${params.ingredientId}/edit`) {
    return [settings, ingredients, ingredientCrumb(labels, params.ingredientId), { label: "Edit" }];
  }
  if (pathname === `/ingredients/${params.ingredientId}`) {
    return [settings, ingredients, { label: labels.ingredientName?.trim() || "Ingredient" }];
  }

  return [];
}
