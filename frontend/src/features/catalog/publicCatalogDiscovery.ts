import type { PublicRecipeMember } from "../../api/publicCatalog";
import { truncateText } from "../dishes/dishVisual";

export type PublicCatalogFilter = "all" | "main" | "centerpieces" | "sides" | "desserts";

export const PUBLIC_CATALOG_FILTERS: PublicCatalogFilter[] = [
  "all",
  "main",
  "centerpieces",
  "sides",
  "desserts",
];

const FILTER_LABELS: Record<PublicCatalogFilter, string> = {
  all: "All",
  main: "Main",
  centerpieces: "Centerpieces",
  sides: "Sides",
  desserts: "Desserts",
};

type SnapshotDish = {
  meal_composition?: string | null;
  simple_dish_part?: string | null;
  course?: string | null;
};

type SnapshotRecipe = {
  recipe_type?: string | null;
  servings?: number | null;
  variant_name?: string | null;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

export function snapshotDish(item: PublicRecipeMember): SnapshotDish {
  return asRecord(item.snapshot.dish) as SnapshotDish;
}

export function snapshotRecipe(item: PublicRecipeMember): SnapshotRecipe {
  return asRecord(item.snapshot.recipe) as SnapshotRecipe;
}

export function publicCatalogFilterLabel(filter: PublicCatalogFilter): string {
  return FILTER_LABELS[filter];
}

export function itemMatchesPublicCatalogFilter(
  item: PublicRecipeMember,
  filter: PublicCatalogFilter,
): boolean {
  if (filter === "all") {
    return true;
  }
  const dish = snapshotDish(item);
  if (filter === "main") {
    return dish.meal_composition === "main_dish";
  }
  if (filter === "centerpieces") {
    return dish.simple_dish_part === "centerpiece";
  }
  if (filter === "sides") {
    return dish.simple_dish_part === "sidedish";
  }
  if (filter === "desserts") {
    return dish.meal_composition === "dessert" || dish.course === "dessert";
  }
  return false;
}

export function filterPublicCatalogItems(
  items: PublicRecipeMember[],
  filter: PublicCatalogFilter,
): PublicRecipeMember[] {
  if (filter === "all") {
    return items;
  }
  return items.filter((item) => itemMatchesPublicCatalogFilter(item, filter));
}

export function normalizePublicCatalogSearch(query: string): string {
  return query.trim().toLowerCase();
}

export function filterPublicCatalogBySearch(
  items: PublicRecipeMember[],
  query: string,
): PublicRecipeMember[] {
  const normalized = normalizePublicCatalogSearch(query);
  if (!normalized) {
    return items;
  }
  return items.filter((item) => {
    const title = item.title.toLowerCase();
    const description = (item.description ?? "").toLowerCase();
    return title.includes(normalized) || description.includes(normalized);
  });
}

function formatCompositionLabel(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  if (value === "main_dish") {
    return "Main";
  }
  if (value === "simple_dish") {
    return "Simple dish";
  }
  if (value === "sidedish") {
    return "Side";
  }
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function publicCatalogCardMeta(item: PublicRecipeMember): string {
  const dish = snapshotDish(item);
  const recipe = snapshotRecipe(item);
  const parts = [
    formatCompositionLabel(dish.meal_composition),
    formatCompositionLabel(dish.simple_dish_part) ?? formatCompositionLabel(dish.course),
    recipe.recipe_type
      ? formatCompositionLabel(recipe.recipe_type)
      : recipe.servings != null
        ? `${recipe.servings} servings`
        : null,
  ].filter(Boolean);
  return parts.join(" · ") || `Version ${item.current_version.version_number}`;
}

export function publicCatalogCardDescription(item: PublicRecipeMember): string | null {
  if (!item.description) {
    return null;
  }
  return truncateText(item.description, 100);
}
