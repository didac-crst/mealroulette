import { useMemo, useState } from "react";

import type { Recipe } from "../../api/catalog";
import type { MealPlanItem, MealSlot } from "../../api/planning";
import { assignMealPlanSlot } from "../../api/planning";
import { ApiError } from "../../api/client";
import {
  BottomSheet,
  Button,
  SearchSelect,
  SegmentedControl,
  WeekdayPicker,
} from "../../components/ui";
import {
  addDays,
  formatPlanDate,
  formatSlotLabel,
  todayIso,
  weekDates,
  weekStartForDate,
} from "./planFormat";
import { WeekNavigator } from "./WeekNavigator";

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
  const recipeOptions = useMemo(
    () =>
      recipes.map((recipe) => ({
        value: String(recipe.id),
        label: `${recipe.variant_name}${recipe.is_main ? " (main)" : ""}`,
      })),
    [recipes],
  );

  if (!open) {
    return null;
  }

  function shiftWeek(nextWeekStart: string) {
    setWeekStart(nextWeekStart);
    setMealDate((current) => {
      const nextDates = weekDates(nextWeekStart).filter((date) => date >= todayIso());
      if (nextDates.includes(current)) {
        return current;
      }
      return nextDates[0] ?? nextWeekStart;
    });
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
    <BottomSheet open={open} titleId="plan-for-meal-title" onClose={onClose}>
      <div className="bottom-sheet-content stack">
        <div className="row-between">
          <h3 id="plan-for-meal-title">Plan for…</h3>
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        <p className="muted">
          Assign <strong>{dishName}</strong> to a lunch or dinner slot.
        </p>

        <WeekNavigator
          weekStart={weekStart}
          loading={busy}
          onPreviousWeek={() => shiftWeek(addDays(weekStart, -7))}
          onThisWeek={() => {
            const currentWeek = weekStartForDate(todayIso());
            shiftWeek(currentWeek);
            setMealDate(todayIso());
          }}
          onNextWeek={() => shiftWeek(addDays(weekStart, 7))}
        />

        <div className="stack">
          <span className="muted">Day</span>
          <WeekdayPicker
            dates={selectableDates}
            value={mealDate}
            onChange={(date) => {
              setMealDate(date);
              setWeekStart(weekStartForDate(date));
            }}
            formatLabel={(date) =>
              new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(new Date(`${date}T12:00:00`))
            }
            formatSubLabel={(date) =>
              new Intl.DateTimeFormat(undefined, { day: "numeric" }).format(new Date(`${date}T12:00:00`))
            }
            disabled={busy}
            ariaLabel="Day"
          />
        </div>

        <SegmentedControl
          className="segmented-control-full"
          ariaLabel="Meal slot"
          value={mealSlot}
          options={[
            { value: "lunch" as const, label: "Lunch" },
            { value: "dinner" as const, label: "Dinner" },
          ]}
          onChange={setMealSlot}
        />

        {recipes.length > 1 ? (
          <label className="meal-slot-assign">
            <span className="muted">Recipe variant</span>
            <SearchSelect
              ariaLabel="Recipe variant"
              value={recipeId}
              options={recipeOptions}
              disabled={busy}
              placeholder="Main recipe"
              emptyLabel="Main recipe"
              allowEmptyOption
              onChange={setRecipeId}
            />
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

        <Button type="button" disabled={busy || selectableDates.length === 0} loading={busy} onClick={() => void handleSubmit()}>
          Add to plan
        </Button>
      </div>
    </BottomSheet>
  );
}
