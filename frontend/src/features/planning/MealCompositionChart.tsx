import { RecipeCompositionChart } from "../dishes/RecipeCompositionChart";

type Props = {
  traits: Record<string, unknown> | null | undefined;
  className?: string;
};

export function MealCompositionChart({ traits, className }: Props) {
  return (
    <RecipeCompositionChart
      traits={traits}
      title="Meal composition"
      hint="Combined food groups from all dishes in this meal, by approximate ingredient weight."
      className={["meal-composition", className].filter(Boolean).join(" ")}
    />
  );
}
