import type { MetadataItem } from "../../components/ui";
import { MetadataList } from "../../components/ui";
import { buildDisplayFoodGroupLabels } from "../../lib/foodGroupComposition";
import { formatTagName } from "./classification";

type Props = {
  traits: Record<string, unknown> | null | undefined;
  emptyMessage?: string;
};

function formatFoodGroups(groups: unknown): string | null {
  if (!Array.isArray(groups) || groups.length === 0) {
    return null;
  }
  return groups.map((group) => formatTagName(String(group))).join(", ");
}

function formatDominant(value: unknown): string | null {
  if (typeof value !== "string" || !value) {
    return null;
  }
  return formatTagName(value);
}

export function buildInferredTraitItems(traits: Record<string, unknown> | null | undefined): MetadataItem[] {
  if (!traits) {
    return [];
  }

  const items: MetadataItem[] = [];
  const weights =
    traits.food_group_weights && typeof traits.food_group_weights === "object"
      ? (traits.food_group_weights as Record<string, unknown>)
      : null;
  const displayFoodGroupLabels = weights
    ? buildDisplayFoodGroupLabels(weights)
    : formatFoodGroups(traits.contains_food_groups)?.split(", ") ?? [];
  const displayFoodGroups = displayFoodGroupLabels.length > 0 ? displayFoodGroupLabels.join(", ") : null;
  const dominantProtein = formatDominant(traits.dominant_protein);
  const dominantCarb = formatDominant(traits.dominant_carb);
  const vegan = traits.vegan === true;
  const carbHeavy = traits.carb_heavy === true;

  if (displayFoodGroups) {
    items.push({ label: "Food groups", value: displayFoodGroups });
  }
  if (dominantProtein) {
    items.push({ label: "Dominant protein", value: dominantProtein });
  }
  if (dominantCarb) {
    items.push({ label: "Dominant carb", value: dominantCarb });
  }
  if (displayFoodGroups || dominantProtein || dominantCarb) {
    items.push({
      label: "Diet",
      value: `${vegan ? "Vegan" : "Not vegan"}${carbHeavy ? " · carb-heavy" : ""}`,
    });
  }

  return items;
}

export function InferredTraitsSummary({
  traits,
  emptyMessage = "Add a main recipe with ingredients to infer fish, meat, pasta, and other weekly targets.",
}: Props) {
  const items = buildInferredTraitItems(traits);
  if (items.length === 0) {
    return <p className="muted">{emptyMessage}</p>;
  }

  return <MetadataList items={items} />;
}
