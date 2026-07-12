export const TARGET_PRESETS = [
  "fish",
  "meat",
  "vegetarian",
  "pasta",
  "rice",
  "soup",
] as const;

const TARGET_LABELS: Record<string, string> = {
  fish: "Fish",
  meat: "Meat",
  vegetarian: "Vegetarian",
  pasta: "Pasta",
  rice: "Rice",
  soup: "Soup",
};

const TARGET_HINTS: Record<string, string> = {
  fish: "Dishes tagged fish",
  meat: "Chicken, beef, pork, lamb, duck, turkey",
  vegetarian: "Legumes, tofu, eggs, cheese, veg-only",
  pasta: "Carb tag pasta",
  rice: "Carb tag rice",
  soup: "Soup style or tag",
};

export function targetLabel(key: string): string {
  return TARGET_LABELS[key] ?? key.replace(/_/g, " ");
}

export function targetHint(key: string): string | null {
  return TARGET_HINTS[key] ?? null;
}
