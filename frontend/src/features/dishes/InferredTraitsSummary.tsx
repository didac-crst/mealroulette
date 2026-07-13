import type { MetadataItem } from "../../components/ui";
import { MetadataList } from "../../components/ui";
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
  const foodGroups = formatFoodGroups(traits.contains_food_groups);
  const dominantProtein = formatDominant(traits.dominant_protein);
  const dominantCarb = formatDominant(traits.dominant_carb);
  const vegan = traits.vegan === true;
  const carbHeavy = traits.carb_heavy === true;

  if (foodGroups) {
    items.push({ label: "Food groups", value: foodGroups });
  }
  if (dominantProtein) {
    items.push({ label: "Dominant protein", value: dominantProtein });
  }
  if (dominantCarb) {
    items.push({ label: "Dominant carb", value: dominantCarb });
  }
  if (foodGroups || dominantProtein || dominantCarb) {
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
