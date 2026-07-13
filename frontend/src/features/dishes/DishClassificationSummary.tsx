import type { Dish, Tag } from "../../api/catalog";
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

export function DishInheritedContext({ dish, tags }: Props) {
  const styles = selectedTagNames(tags, dish.tag_ids, "style");
  const mealSlots: string[] = [];
  if (dish.suitable_for_lunch) {
    mealSlots.push("lunch");
  }
  if (dish.suitable_for_dinner) {
    mealSlots.push("dinner");
  }

  return (
    <aside className="inherited-context stack">
      <h3 className="section-title">Inherited from dish</h3>
      <p>
        <span className="muted">Meal composition: </span>
        {formatOptionLabel(MEAL_COMPOSITION_OPTIONS, dish.meal_composition)}
        {dish.meal_composition === "simple_dish" && dish.simple_dish_part
          ? ` (${formatOptionLabel(SIMPLE_DISH_PART_OPTIONS, dish.simple_dish_part)})`
          : ""}
      </p>
      <InferredTraitsSummary traits={dish.computed_traits_json} />
      {styles.length > 0 ? (
        <p>
          <span className="muted">Curated style: </span>
          {joinLabels(styles, STYLE_OPTIONS)}
        </p>
      ) : null}
      <p>
        <span className="muted">Suitable for: </span>
        {mealSlots.length > 0 ? mealSlots.join(", ") : "Not set"}
      </p>
      <p>
        <span className="muted">Default time: </span>
        {dish.default_prep_time_minutes ?? "—"} / {dish.default_cook_time_minutes ?? "—"} min
      </p>
      <p>
        <span className="muted">Default difficulty: </span>
        {formatDifficulty(dish.default_difficulty)}
      </p>
      {dish.kids_friendly ? <p className="muted">Kids-friendly dish</p> : null}
    </aside>
  );
}

export function DishClassificationSummary({ dish, tags }: Props) {
  const styles = selectedTagNames(tags, dish.tag_ids, "style");

  const mealSlots: string[] = [];
  if (dish.suitable_for_lunch) {
    mealSlots.push("lunch");
  }
  if (dish.suitable_for_dinner) {
    mealSlots.push("dinner");
  }

  return (
    <div className="classification-summary stack">
      <div>
        <h3 className="section-title">Classification</h3>
        <p>
          <span className="muted">Meal composition: </span>
          {formatOptionLabel(MEAL_COMPOSITION_OPTIONS, dish.meal_composition)}
          {dish.meal_composition === "simple_dish" && dish.simple_dish_part
            ? ` (${formatOptionLabel(SIMPLE_DISH_PART_OPTIONS, dish.simple_dish_part)})`
            : ""}
        </p>
        <InferredTraitsSummary traits={dish.computed_traits_json} />
        {styles.length > 0 ? (
          <p>
            <span className="muted">Curated style: </span>
            {joinLabels(styles, STYLE_OPTIONS)}
          </p>
        ) : null}
      </div>
      <div>
        <h3 className="section-title">Planning profile</h3>
        <p>
          <span className="muted">Suitable for: </span>
          {mealSlots.length > 0 ? mealSlots.join(", ") : "Not set"}
        </p>
        <p>
          <span className="muted">Weekday-friendly: </span>
          {dish.weekday_friendly == null ? "Not set" : dish.weekday_friendly ? "Yes" : "No"}
        </p>
        <p>
          <span className="muted">Kids-friendly: </span>
          {dish.kids_friendly == null ? "Not set" : dish.kids_friendly ? "Yes" : "No"}
        </p>
        <p>
          <span className="muted">Leftovers: </span>
          {dish.leftovers_possible == null ? "Not set" : dish.leftovers_possible ? "Possible" : "No"}
        </p>
        <p>
          <span className="muted">Freezer-friendly: </span>
          {dish.freezer_friendly == null ? "Unknown" : dish.freezer_friendly ? "Yes" : "No"}
        </p>
        <p>
          <span className="muted">Thermomix possible: </span>
          {dish.thermomix_possible == null ? "No recipes yet" : dish.thermomix_possible ? "Yes" : "No"}
        </p>
        <p>
          <span className="muted">Difficulty (main recipe): </span>
          {formatDifficulty(dish.default_difficulty)}
        </p>
        <p>
          <span className="muted">Prep / cook (main recipe): </span>
          {dish.default_prep_time_minutes ?? "—"} / {dish.default_cook_time_minutes ?? "—"} min
        </p>
      </div>
      {dish.seasonality ? (
        <div>
          <h3 className="section-title">Seasonality</h3>
          <p>
            <span className="muted">Mode: </span>
            {formatOptionLabel(SEASONALITY_MODE_OPTIONS, dish.seasonality.seasonality_mode)}
          </p>
          {dish.seasonality.seasonality_mode === "seasonal" && dish.seasonality.preferred_months.length > 0 ? (
            <p>
              <span className="muted">Preferred months: </span>
              {dish.seasonality.preferred_months
                .map((month) => MONTH_OPTIONS.find((option) => option.value === month)?.label ?? month)
                .join(", ")}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
