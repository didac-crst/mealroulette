import { useMemo, useState } from "react";

import type { Recipe } from "../../api/catalog";
import type { MealPlanItem, MealSlot } from "../../api/planning";
import { assignMealPlanSlot } from "../../api/planning";
import { ApiError } from "../../api/client";
import { addDays, formatPlanDate, formatSlotLabel, todayIso, weekDates, weekStartForDate } from "./planFormat";

type Props = {
  open: boolean;
  dishId: number;
  dishName: string;
  recipes: Recipe[];
  accessToken: string;
  onClose: () => void;
  onAssigned?: (item: MealPlanItem, weekStart: string) => void;
};

export function PlanForMealDialog({
  open,
  dishId,
  dishName,
  recipes,
  accessToken,
  onClose,
  onAssigned,
}: Props) {
  const [weekStart, setWeekStart] = useState(() => weekStartForDate(todayIso()));
  const [mealDate, setMealDate] = useState(() => todayIso());
  const [mealSlot, setMealSlot] = useState<MealSlot>("dinner");
  const [recipeId, setRecipeId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const dates = useMemo(() => weekDates(weekStart), [weekStart]);
  const selectableDates = useMemo(() => dates.filter((date) => date >= todayIso()), [dates]);

  if (!open) {
    return null;
  }

  async function handleSubmit() {
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const item = await assignMealPlanSlot(accessToken, {
        date: mealDate,
        meal_slot: mealSlot,
        dish_id: dishId,
        recipe_id: recipeId ? Number(recipeId) : null,
      });
      const assignedWeek = weekStartForDate(item.date);
      setSuccess(`Planned for ${formatPlanDate(item.date)} · ${formatSlotLabel(item.meal_slot)}`);
      onAssigned?.(item, assignedWeek);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to plan meal");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal-card stack"
        role="dialog"
        aria-labelledby="plan-for-meal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="row-between">
          <h3 id="plan-for-meal-title">Plan for…</h3>
          <button type="button" className="button button-secondary" onClick={onClose}>
            Close
          </button>
        </div>
        <p className="muted">
          Assign <strong>{dishName}</strong> to a lunch or dinner slot.
        </p>

        <div className="week-nav" role="group" aria-label="Plan week">
          <button
            type="button"
            className="button button-secondary week-nav-button"
            disabled={busy}
            onClick={() => {
              const previous = addDays(weekStart, -7);
              setWeekStart(previous);
              setMealDate((current) => (weekDates(previous).includes(current) ? current : previous));
            }}
          >
            ‹ Prev week
          </button>
          <span className="muted week-nav-label">Week of {formatPlanDate(weekStart)}</span>
          <button
            type="button"
            className="button button-secondary week-nav-button"
            disabled={busy}
            onClick={() => {
              const next = addDays(weekStart, 7);
              setWeekStart(next);
              const firstFuture = weekDates(next).find((date) => date >= todayIso()) ?? next;
              setMealDate(firstFuture);
            }}
          >
            Next week ›
          </button>
        </div>

        <label>
          Day
          <select
            value={mealDate}
            disabled={busy}
            onChange={(event) => {
              setMealDate(event.target.value);
              setWeekStart(weekStartForDate(event.target.value));
            }}
          >
            {selectableDates.map((date) => (
              <option key={date} value={date}>
                {formatPlanDate(date)}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="meal-slot-toggle">
          <legend className="muted">Meal</legend>
          <label>
            <input
              type="radio"
              name="meal-slot"
              value="lunch"
              checked={mealSlot === "lunch"}
              disabled={busy}
              onChange={() => setMealSlot("lunch")}
            />
            Lunch
          </label>
          <label>
            <input
              type="radio"
              name="meal-slot"
              value="dinner"
              checked={mealSlot === "dinner"}
              disabled={busy}
              onChange={() => setMealSlot("dinner")}
            />
            Dinner
          </label>
        </fieldset>

        {recipes.length > 1 ? (
          <label>
            Recipe variant
            <select value={recipeId} disabled={busy} onChange={(event) => setRecipeId(event.target.value)}>
              <option value="">Main recipe</option>
              {recipes.map((recipe) => (
                <option key={recipe.id} value={recipe.id}>
                  {recipe.variant_name}
                  {recipe.is_main ? " (main)" : ""}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="success" role="status">
            {success}
          </p>
        ) : null}

        <div className="row-actions">
          <button type="button" className="button" disabled={busy || selectableDates.length === 0} onClick={() => void handleSubmit()}>
            {busy ? "Saving…" : "Add to plan"}
          </button>
        </div>
      </div>
    </div>
  );
}
