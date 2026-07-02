import type { Dish, Tag } from "../../api/catalog";
import {
  CARB_OPTIONS,
  COURSE_OPTIONS,
  MONTH_OPTIONS,
  PROTEIN_OPTIONS,
  STYLE_OPTIONS,
  TEMPERATURE_OPTIONS,
  formatOptionLabel,
  formatTagName,
  selectedTagNames,
} from "./classification";
import { formatDifficulty } from "./constants";

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
  const proteins = selectedTagNames(tags, dish.tag_ids, "protein");
  const carbs = selectedTagNames(tags, dish.tag_ids, "carb");
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
        <span className="muted">Course: </span>
        {formatOptionLabel(COURSE_OPTIONS, dish.course ?? "")}
      </p>
      <p>
        <span className="muted">Food profile: </span>
        {[joinLabels(proteins, PROTEIN_OPTIONS), joinLabels(carbs, CARB_OPTIONS)].filter((v) => v !== "Not set").join(" · ") || "Not set"}
      </p>
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
  const proteins = selectedTagNames(tags, dish.tag_ids, "protein");
  const carbs = selectedTagNames(tags, dish.tag_ids, "carb");
  const styles = selectedTagNames(tags, dish.tag_ids, "style");
  const temperatures = selectedTagNames(tags, dish.tag_ids, "temperature");

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
        <h3 className="section-title">Food profile</h3>
        <p>
          <span className="muted">Course: </span>
          {formatOptionLabel(COURSE_OPTIONS, dish.course ?? "")}
        </p>
        <p>
          <span className="muted">Protein / source: </span>
          {joinLabels(proteins, PROTEIN_OPTIONS)}
        </p>
        <p>
          <span className="muted">Carb / base: </span>
          {joinLabels(carbs, CARB_OPTIONS)}
        </p>
        {styles.length > 0 ? (
          <p>
            <span className="muted">Style: </span>
            {joinLabels(styles, STYLE_OPTIONS)}
          </p>
        ) : null}
        {temperatures.length > 0 ? (
          <p>
            <span className="muted">Temperature: </span>
            {joinLabels(temperatures, TEMPERATURE_OPTIONS)}
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
            {formatTagName(dish.seasonality.seasonality_mode)}
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
      <p className="muted">Dietary information is inferred from recipe ingredients.</p>
    </div>
  );
}
