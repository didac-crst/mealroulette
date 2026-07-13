import type { Tag } from "../../api/catalog";

export const STRUCTURED_TAG_FAMILIES = ["protein", "carb", "style", "temperature"] as const;

/** Dish-level tags that are not inferred from recipe ingredients (e.g. soup). */
export const CURATED_DISH_TAG_FAMILIES = ["style"] as const;

export const RECIPE_TYPE_OPTIONS = [
  { value: "standard", label: "Standard" },
  { value: "thermomix", label: "Thermomix" },
  { value: "other_appliance", label: "Other appliance" },
] as const;

export type StructuredTagFamily = (typeof STRUCTURED_TAG_FAMILIES)[number];

export const COURSE_OPTIONS = [
  { value: "", label: "Not set" },
  { value: "starter", label: "Starter" },
  { value: "main", label: "Main" },
  { value: "dessert", label: "Dessert" },
] as const;

export const MEAL_COMPOSITION_OPTIONS = [
  { value: "main_dish", label: "Main dish" },
  { value: "simple_dish", label: "Simple dish" },
  { value: "dessert", label: "Dessert" },
] as const;

export const SIMPLE_DISH_PART_OPTIONS = [
  { value: "centerpiece", label: "Centerpiece" },
  { value: "sidedish", label: "Side dish" },
] as const;

export const STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "active", label: "Active" },
  { value: "archived", label: "Archived" },
] as const;

export const PROTEIN_OPTIONS = [
  { value: "none_vegetables", label: "None / mostly vegetables" },
  { value: "chicken", label: "Chicken" },
  { value: "turkey", label: "Turkey" },
  { value: "beef", label: "Beef" },
  { value: "pork", label: "Pork" },
  { value: "lamb", label: "Lamb" },
  { value: "duck", label: "Duck" },
  { value: "fish", label: "Fish" },
  { value: "seafood", label: "Seafood" },
  { value: "eggs", label: "Eggs" },
  { value: "cheese_dairy", label: "Cheese / dairy" },
  { value: "legumes", label: "Legumes / lentils / beans" },
  { value: "tofu_soy", label: "Tofu / soy" },
  { value: "mixed", label: "Mixed" },
  { value: "other", label: "Other" },
] as const;

export const CARB_OPTIONS = [
  { value: "pasta", label: "Pasta" },
  { value: "rice", label: "Rice" },
  { value: "potato", label: "Potato" },
  { value: "sweet_potato", label: "Sweet potato" },
  { value: "bread_dough_pastry", label: "Bread / dough / pastry" },
  { value: "couscous_semolina", label: "Couscous / semolina" },
  { value: "quinoa", label: "Quinoa" },
  { value: "noodles", label: "Noodles" },
  { value: "legumes", label: "Legumes" },
  { value: "other", label: "Other" },
] as const;

export const TEMPERATURE_OPTIONS = [
  { value: "hot", label: "Hot" },
  { value: "cold", label: "Cold" },
] as const;

export const STYLE_OPTIONS = [
  { value: "soup", label: "Soup" },
  { value: "stew", label: "Stew" },
  { value: "oven", label: "Oven dish" },
  { value: "gratin", label: "Gratin" },
  { value: "curry", label: "Curry" },
  { value: "salad", label: "Salad" },
  { value: "tart_quiche", label: "Tart / quiche" },
  { value: "pasta_dish", label: "Pasta dish" },
  { value: "rice_dish", label: "Rice dish" },
  { value: "bowl", label: "Bowl" },
  { value: "wok", label: "Wok" },
  { value: "fried", label: "Fried" },
  { value: "dip_spread", label: "Dip / spread" },
] as const;

export const SEASONALITY_MODE_OPTIONS = [
  { value: "all_year", label: "All year" },
  { value: "seasonal", label: "Seasonal" },
] as const;

export const MONTH_OPTIONS = [
  { value: 1, label: "Jan" },
  { value: 2, label: "Feb" },
  { value: 3, label: "Mar" },
  { value: 4, label: "Apr" },
  { value: 5, label: "May" },
  { value: 6, label: "Jun" },
  { value: 7, label: "Jul" },
  { value: 8, label: "Aug" },
  { value: 9, label: "Sep" },
  { value: 10, label: "Oct" },
  { value: 11, label: "Nov" },
  { value: 12, label: "Dec" },
] as const;

export function formatOptionLabel(
  options: ReadonlyArray<{ value: string; label: string }>,
  value: string | null | undefined,
): string {
  if (!value) {
    return "Not set";
  }
  return options.find((option) => option.value === value)?.label ?? value.replace(/_/g, " ");
}

export function tagKey(tag: Pick<Tag, "family" | "name">): string {
  return `${tag.family}:${tag.name}`;
}

export function findTagId(tags: Tag[], family: string, name: string): number | undefined {
  return tags.find((tag) => tag.family === family && tag.name === name)?.id;
}

export function selectedTagNames(tags: Tag[], tagIds: number[], family: string): string[] {
  const idSet = new Set(tagIds);
  return tags.filter((tag) => tag.family === family && idSet.has(tag.id)).map((tag) => tag.name);
}

export function curatedDishTagIds(tagIds: number[], tags: Tag[]): number[] {
  const allowedFamilies = new Set<string>(CURATED_DISH_TAG_FAMILIES);
  const allowedIds = new Set(tags.filter((tag) => allowedFamilies.has(tag.family)).map((tag) => tag.id));
  return tagIds.filter((id) => allowedIds.has(id));
}

export function formatTagName(name: string): string {
  return name.replace(/_/g, " ");
}
