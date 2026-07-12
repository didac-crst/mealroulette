export function formatComputedTraits(
  traits: Record<string, unknown> | null | undefined,
): string | null {
  if (!traits) {
    return null;
  }
  const parts = [
    traits.vegan ? "vegan" : "not vegan",
    traits.carb_heavy ? "carb-heavy" : null,
    traits.dominant_protein ? `protein ${String(traits.dominant_protein)}` : null,
    traits.dominant_carb ? `carb ${String(traits.dominant_carb)}` : null,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : null;
}
