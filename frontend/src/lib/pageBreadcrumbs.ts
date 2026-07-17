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

function entityCrumb(
  labelId: number | null | undefined,
  paramId: string | undefined,
  name: string | null | undefined,
  fallbackLabel: string,
  toPrefix: string,
): BreadcrumbItem {
  const id = labelId ?? (paramId ? Number(paramId) : null);
  const label = name?.trim() || fallbackLabel;
  return id ? { label, to: `${toPrefix}/${id}` } : { label };
}

function dishCrumb(labels: BreadcrumbLabels, dishId?: string): BreadcrumbItem {
  return entityCrumb(labels.dishId, dishId, labels.dishName, "Dish", "/dishes");
}

function ingredientCrumb(labels: BreadcrumbLabels, ingredientId?: string): BreadcrumbItem {
  return entityCrumb(labels.ingredientId, ingredientId, labels.ingredientName, "Ingredient", "/ingredients");
}

function recipeCrumb(labels: BreadcrumbLabels, dishId?: string, recipeId?: string): BreadcrumbItem {
  const id = labels.recipeId ?? (recipeId ? Number(recipeId) : null);
  const label = labels.recipeName?.trim() || "Recipe";
  const dish = labels.dishId ?? (dishId ? Number(dishId) : null);
  return id && dish ? { label, to: `/dishes/${dish}/recipes/${id}` } : { label };
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
    return [dishes, dishCrumb(labels, params.dishId), recipeCrumb(labels, params.dishId, params.recipeId), { label: "Edit" }];
  }
  if (pathname === `/dishes/${params.dishId}/recipes/${params.recipeId}`) {
    return [dishes, dishCrumb(labels, params.dishId), recipeCrumb(labels, params.dishId, params.recipeId)];
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
  if (pathname === "/settings/members") {
    return [settings, { label: "Household settings" }];
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
  if (pathname === "/settings/password") {
    return [settings, { label: "Password" }];
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
