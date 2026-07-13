import type { Dish, Tag } from "../../api/catalog";
import { Card, MetadataList } from "../../components/ui";
import {
  MEAL_COMPOSITION_OPTIONS,
  MONTH_OPTIONS,
  SEASONALITY_MODE_OPTIONS,
  SIMPLE_DISH_PART_OPTIONS,
  STYLE_OPTIONS,
  formatOptionLabel,
  selectedTagNames,
} from "./classification";
import { formatDifficulty } from "./constants";
import { InferredTraitsSummary } from "./InferredTraitsSummary";

type Props = {
  dish: Dish;
  tags: Tag[];
};

function joinLabels(values: string[], options: ReadonlyArray<{ value: string; label: string }>): string {
  if (values.length === 0) {
    return "Not set";
  }
  return values.map((value) => formatOptionLabel(options, value)).join(", ");
}

function yesNo(value: boolean | null | undefined, unset = "Not set"): string {
  if (value == null) {
    return unset;
  }
  return value ? "Yes" : "No";
}

export function DishInheritedContext({ dish, tags }: Props) {
  const styles = selectedTagNames(tags, dish.tag_ids, "style");
  const mealSlots: string[] = [];
  if (dish.suitable_for_lunch) {
    mealSlots.push("Lunch");
  }
  if (dish.suitable_for_dinner) {
    mealSlots.push("Dinner");
  }

  return (
    <aside className="inherited-context stack">
      <h3 className="section-title">Inherited from dish</h3>
      <MetadataList
        items={[
          {
            label: "Meal composition",
            value: (
              <>
                {formatOptionLabel(MEAL_COMPOSITION_OPTIONS, dish.meal_composition)}
                {dish.meal_composition === "simple_dish" && dish.simple_dish_part
                  ? ` (${formatOptionLabel(SIMPLE_DISH_PART_OPTIONS, dish.simple_dish_part)})`
                  : ""}
              </>
            ),
          },
          ...(styles.length > 0
            ? [{ label: "Curated style", value: joinLabels(styles, STYLE_OPTIONS) }]
            : []),
          { label: "Suitable for", value: mealSlots.length > 0 ? mealSlots.join(", ") : "Not set" },
          {
            label: "Default time",
            value: `${dish.default_prep_time_minutes ?? "—"} / ${dish.default_cook_time_minutes ?? "—"} min`,
          },
          { label: "Default difficulty", value: formatDifficulty(dish.default_difficulty) },
          ...(dish.kids_friendly ? [{ label: "Kids-friendly", value: "Yes" }] : []),
        ]}
      />
      <InferredTraitsSummary traits={dish.computed_traits_json} />
    </aside>
  );
}

export function DishClassificationSummary({ dish, tags }: Props) {
  const styles = selectedTagNames(tags, dish.tag_ids, "style");
  const mealSlots: string[] = [];
  if (dish.suitable_for_lunch) {
    mealSlots.push("Lunch");
  }
  if (dish.suitable_for_dinner) {
    mealSlots.push("Dinner");
  }

  return (
    <Card density="comfortable" className="classification-summary stack">
      <div>
        <h2 className="catalog-section-title">Classification</h2>
        <MetadataList
          items={[
            {
              label: "Meal composition",
              value: (
                <>
                  {formatOptionLabel(MEAL_COMPOSITION_OPTIONS, dish.meal_composition)}
                  {dish.meal_composition === "simple_dish" && dish.simple_dish_part
                    ? ` (${formatOptionLabel(SIMPLE_DISH_PART_OPTIONS, dish.simple_dish_part)})`
                    : ""}
                </>
              ),
            },
            ...(styles.length > 0
              ? [{ label: "Curated style", value: joinLabels(styles, STYLE_OPTIONS) }]
              : []),
          ]}
        />
        <InferredTraitsSummary traits={dish.computed_traits_json} />
      </div>
      <div>
        <h3 className="section-title">Planning profile</h3>
        <MetadataList
          items={[
            { label: "Suitable for", value: mealSlots.length > 0 ? mealSlots.join(", ") : "Not set" },
            { label: "Weekday-friendly", value: yesNo(dish.weekday_friendly) },
            { label: "Kids-friendly", value: yesNo(dish.kids_friendly) },
            {
              label: "Leftovers",
              value: dish.leftovers_possible == null ? "Not set" : dish.leftovers_possible ? "Possible" : "No",
            },
            { label: "Freezer-friendly", value: yesNo(dish.freezer_friendly, "Unknown") },
            {
              label: "Thermomix possible",
              value: dish.thermomix_possible == null ? "No recipes yet" : yesNo(dish.thermomix_possible),
            },
            { label: "Difficulty (main recipe)", value: formatDifficulty(dish.default_difficulty) },
            {
              label: "Prep / cook (main recipe)",
              value: `${dish.default_prep_time_minutes ?? "—"} / ${dish.default_cook_time_minutes ?? "—"} min`,
            },
          ]}
        />
      </div>
      {dish.seasonality ? (
        <div>
          <h3 className="section-title">Seasonality</h3>
          <MetadataList
            items={[
              {
                label: "Mode",
                value: formatOptionLabel(SEASONALITY_MODE_OPTIONS, dish.seasonality.seasonality_mode),
              },
              ...(dish.seasonality.seasonality_mode === "seasonal" &&
              dish.seasonality.preferred_months.length > 0
                ? [
                    {
                      label: "Preferred months",
                      value: dish.seasonality.preferred_months
                        .map((month) => MONTH_OPTIONS.find((option) => option.value === month)?.label ?? month)
                        .join(", "),
                    },
                  ]
                : []),
            ]}
          />
        </div>
      ) : null}
    </Card>
  );
}
