import { buildCompositionChartData, compositionConicGradient } from "../../lib/foodGroupComposition";

const CHART_COLORS = [
  "var(--brand-teal-500)",
  "var(--brand-orange-500)",
  "var(--brand-green-500)",
  "var(--info-600)",
  "var(--brand-teal-700)",
  "var(--warning-600)",
  "var(--ink-500)",
] as const;

export type RecipeCompositionChartProps = {
  traits: Record<string, unknown> | null | undefined;
  title?: string;
  hint?: string;
  className?: string;
};

export function RecipeCompositionChart({
  traits,
  title = "Food group composition",
  hint = "Based on recipe ingredients by approximate weight. Very small amounts are omitted.",
  className,
}: RecipeCompositionChartProps) {
  const weights = traits?.food_group_weights;
  const chart = buildCompositionChartData(
    weights && typeof weights === "object" ? (weights as Record<string, unknown>) : null,
  );
  const gradient = compositionConicGradient(chart.slices, CHART_COLORS);

  if (!chart.hasData || !gradient) {
    return (
      <section className={["recipe-composition", className].filter(Boolean).join(" ")} aria-label={title}>
        <h3 className="classification-summary-heading">{title}</h3>
        <p className="muted recipe-composition-empty">
          No composition yet. Add recipe ingredients with quantities to calculate food groups.
        </p>
      </section>
    );
  }

  const accessibleSummary = chart.slices
    .map((slice) => `${slice.label} ${Math.round(slice.percent)}%`)
    .join(", ");

  return (
    <section className={["recipe-composition", className].filter(Boolean).join(" ")} aria-label={title}>
      <h3 className="classification-summary-heading">{title}</h3>
      <p className="muted recipe-composition-hint">{hint}</p>
      <div className="recipe-composition-body">
        <div
          className="recipe-composition-chart"
          role="img"
          aria-label={`${title}: ${accessibleSummary}`}
          style={{ background: gradient }}
        >
          <span className="recipe-composition-chart-center">100%</span>
        </div>
        <ul className="recipe-composition-legend">
          {chart.slices.map((slice, index) => (
            <li key={slice.key} className="recipe-composition-legend-item">
              <span
                className="recipe-composition-swatch"
                style={{ background: CHART_COLORS[index % CHART_COLORS.length] }}
                aria-hidden
              />
              <span className="recipe-composition-legend-label">{slice.label}</span>
              <span className="recipe-composition-legend-value">{Math.round(slice.percent)}%</span>
            </li>
          ))}
        </ul>
      </div>
      <p className="visually-hidden">{accessibleSummary}</p>
    </section>
  );
}
