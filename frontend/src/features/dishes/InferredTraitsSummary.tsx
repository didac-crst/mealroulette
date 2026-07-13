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

export function InferredTraitsSummary({
  traits,
  emptyMessage = "Add a main recipe with ingredients to infer fish, meat, pasta, and other weekly targets.",
}: Props) {
  if (!traits) {
    return <p className="muted">{emptyMessage}</p>;
  }

  const foodGroups = formatFoodGroups(traits.contains_food_groups);
  const dominantProtein = formatDominant(traits.dominant_protein);
  const dominantCarb = formatDominant(traits.dominant_carb);
  const vegan = traits.vegan === true;
  const carbHeavy = traits.carb_heavy === true;

  if (!foodGroups && !dominantProtein && !dominantCarb) {
    return <p className="muted">{emptyMessage}</p>;
  }

  return (
    <div className="inferred-traits stack">
      {foodGroups ? (
        <p>
          <span className="muted">Food groups: </span>
          {foodGroups}
        </p>
      ) : null}
      {dominantProtein ? (
        <p>
          <span className="muted">Dominant protein: </span>
          {dominantProtein}
        </p>
      ) : null}
      {dominantCarb ? (
        <p>
          <span className="muted">Dominant carb: </span>
          {dominantCarb}
        </p>
      ) : null}
      <p>
        <span className="muted">Diet: </span>
        {vegan ? "Vegan" : "Not vegan"}
        {carbHeavy ? " · carb-heavy" : ""}
      </p>
    </div>
  );
}
