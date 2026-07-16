export const AGGREGATION_STRATEGIES = [
  { value: "", label: "Default" },
  { value: "strict_same_dimension", label: "Strict same dimension" },
  { value: "prefer_mass", label: "Prefer mass" },
  { value: "prefer_volume", label: "Prefer volume" },
  { value: "prefer_count", label: "Prefer count" },
  { value: "allow_approximate_conversion", label: "Allow approximate conversion" },
  { value: "never_convert_count", label: "Never convert count" },
] as const;

const LABELS = Object.fromEntries(
  AGGREGATION_STRATEGIES.filter((option) => option.value).map((option) => [option.value, option.label]),
) as Record<string, string>;

/** Turn snake_case catalog values into readable labels (category, food group, family, …). */
export function formatCatalogLabel(value: string | null | undefined): string {
  if (!value?.trim()) {
    return "—";
  }
  const spaced = value.trim().replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function formatAggregationStrategy(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  return LABELS[value] ?? formatCatalogLabel(value);
}
