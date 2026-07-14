export type CompositionSlice = {
  key: string;
  label: string;
  percent: number;
};

export type CompositionChartData = {
  slices: CompositionSlice[];
  hasData: boolean;
};

const DEFAULT_THRESHOLD = 10;

export function formatFoodGroupLabel(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function buildCompositionChartData(
  weights: Record<string, unknown> | null | undefined,
  threshold = DEFAULT_THRESHOLD,
): CompositionChartData {
  if (!weights) {
    return { slices: [], hasData: false };
  }

  const entries = Object.entries(weights)
    .map(([key, value]) => ({
      key,
      label: formatFoodGroupLabel(key),
      percent: typeof value === "number" ? value : Number(value),
    }))
    .filter((entry) => Number.isFinite(entry.percent) && entry.percent > 0);

  if (entries.length === 0) {
    return { slices: [], hasData: false };
  }

  const major = entries
    .filter((entry) => entry.percent >= threshold)
    .sort((a, b) => b.percent - a.percent);
  const minorTotal = entries
    .filter((entry) => entry.percent < threshold)
    .reduce((sum, entry) => sum + entry.percent, 0);

  const slices = [...major];
  if (minorTotal > 0) {
    slices.push({ key: "other", label: "Other", percent: minorTotal });
  }

  return { slices, hasData: slices.length > 0 };
}

export function buildDisplayFoodGroupLabels(
  weights: Record<string, unknown> | null | undefined,
  threshold = DEFAULT_THRESHOLD,
): string[] {
  return buildCompositionChartData(weights, threshold).slices.map((slice) => slice.label);
}

export function compositionConicGradient(
  slices: CompositionSlice[],
  colors: readonly string[],
): string | null {
  if (slices.length === 0) {
    return null;
  }

  let cursor = 0;
  const stops: string[] = [];
  slices.forEach((slice, index) => {
    const start = cursor;
    cursor += slice.percent;
    const color = colors[index % colors.length];
    stops.push(`${color} ${start}% ${cursor}%`);
  });

  return `conic-gradient(${stops.join(", ")})`;
}
