import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { Dish, Recipe } from "../../api/catalog";
import { fetchRecipes } from "../../api/catalog";
import { ApiError } from "../../api/client";
import {
  addMealPlanLine,
  deleteMealPlanLine,
  markMealDoNotPlan,
  reopenMealSlot,
  type MealPlanItem,
} from "../../api/planning";
import { Button, SearchSelect, SegmentedControl } from "../../components/ui";
import {
  filterDishesByMealLineRole,
  formatMealLineRole,
  formatMealLineSource,
  mealLineRoleFilterLabel,
  mealLineRoleFilterOptions,
  suggestedMealLineRoleFilter,
  type MealLineRoleFilter,
} from "./mealLineFilters";
import {
  formatSlotLabel,
  isFutureMealDate,
  sortedMealLines,
} from "./planFormat";

type Props = {
  item: MealPlanItem;
  dishes: Dish[];
  accessToken: string;
  disabled?: boolean;
  onChanged: (item: MealPlanItem) => void;
  onError: (message: string) => void;
};

export function MealSlotLinesSummary({ item }: { item: MealPlanItem }) {
  const lines = sortedMealLines(item);
  if (lines.length === 0) {
    return null;
  }

  return (
    <ul className="meal-slot-lines">
      {lines.map((line) => (
        <li key={line.id} className="meal-slot-line">
          <div className="meal-slot-line-main">
            {line.dish_id ? (
              <Link to={`/dishes/${line.dish_id}`} className="meal-slot-line-dish">
                {line.dish_name}
              </Link>
            ) : (
              <span className="muted">Unknown dish</span>
            )}
            <span className="meal-slot-line-meta muted">
              {formatMealLineSource(line.source)} · {formatMealLineRole(line.role)}
            </span>
          </div>
          {line.recipe_variant_name ? (
            <p className="muted meal-slot-line-recipe">{line.recipe_variant_name}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function MealSlotPlanEditor({
  item,
  dishes,
  accessToken,
  disabled = false,
  onChanged,
  onError,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [roleFilter, setRoleFilter] = useState<MealLineRoleFilter>(() => suggestedMealLineRoleFilter(item));
  const [dishId, setDishId] = useState("");
  const [recipeId, setRecipeId] = useState("");
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [recipesLoading, setRecipesLoading] = useState(false);

  const lines = sortedMealLines(item);
  const isFuture = isFutureMealDate(item.date);
  const isDoNotPlan = item.planning_state === "do_not_plan";
  const actionDisabled = disabled || busy || item.is_locked || isDoNotPlan;
  const canModifyPlanning = !item.is_locked && !isDoNotPlan;

  const filteredDishes = useMemo(
    () => filterDishesByMealLineRole(dishes, roleFilter),
    [dishes, roleFilter],
  );
  const dishOptions = useMemo(
    () => filteredDishes.map((entry) => ({ value: String(entry.id), label: entry.name })),
    [filteredDishes],
  );
  const recipeOptions = useMemo(
    () =>
      recipes.map((recipe) => ({
        value: String(recipe.id),
        label: `${recipe.variant_name}${recipe.is_main ? " (main)" : ""}`,
      })),
    [recipes],
  );

  useEffect(() => {
    if (!addOpen && lines.length === 0) {
      setRoleFilter(suggestedMealLineRoleFilter(item));
    }
  }, [addOpen, item, lines.length]);

  useEffect(() => {
    if (!dishId) {
      setRecipes([]);
      setRecipesLoading(false);
      return;
    }
    let cancelled = false;
    setRecipesLoading(true);
    fetchRecipes(accessToken, Number(dishId))
      .then((data) => {
        if (!cancelled) {
          setRecipes(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRecipes([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setRecipesLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, dishId]);

  async function run(action: () => Promise<MealPlanItem>) {
    setBusy(true);
    try {
      onChanged(await action());
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function submitDishSelection() {
    if (!dishId) {
      return;
    }
    const payload = {
      dish_id: Number(dishId),
      recipe_id: recipeId ? Number(recipeId) : null,
    };
    await run(() => addMealPlanLine(accessToken, item.id, payload));
    setDishId("");
    setRecipeId("");
    setAddOpen(false);
  }

  async function removeLine(lineId: number) {
    await run(() => deleteMealPlanLine(accessToken, lineId));
  }

  async function handleDoNotPlan() {
    const removeExistingLines =
      lines.length === 0 ||
      window.confirm(
        `Mark ${formatSlotLabel(item.meal_slot)} on ${item.date} as not planning? This removes ${lines.length} dish line(s).`,
      );
    if (!removeExistingLines) {
      return;
    }
    await run(() => markMealDoNotPlan(accessToken, item.id, true));
  }

  if (isDoNotPlan) {
    return (
      <div className="meal-slot-plan-editor stack">
        <p className="muted">This slot is marked as not planning.</p>
        {isFuture ? (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={actionDisabled || item.is_locked}
            onClick={() => void run(() => reopenMealSlot(accessToken, item.id))}
          >
            Reopen slot
          </Button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="meal-slot-plan-editor stack">
      {lines.length > 0 ? (
        <ul className="meal-slot-lines meal-slot-lines-editable">
          {lines.map((line) => (
            <li key={line.id} className="meal-slot-line">
              <div className="meal-slot-line-main">
                {line.dish_id ? (
                  <Link to={`/dishes/${line.dish_id}`} className="meal-slot-line-dish">
                    {line.dish_name}
                  </Link>
                ) : (
                  <span className="muted">Unknown dish</span>
                )}
                <span className="meal-slot-line-meta muted">
                  {formatMealLineSource(line.source)} · {formatMealLineRole(line.role)}
                </span>
              </div>
              {line.recipe_variant_name ? (
                <p className="muted meal-slot-line-recipe">{line.recipe_variant_name}</p>
              ) : null}
              {canModifyPlanning ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={actionDisabled}
                  onClick={() => void removeLine(line.id)}
                >
                  Remove
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      {canModifyPlanning && (lines.length === 0 || addOpen) ? (
        <div className="meal-slot-add-form stack">
          {lines.length > 0 ? (
            <p className="section-title">Add dish to {formatSlotLabel(item.meal_slot).toLowerCase()}</p>
          ) : (
            <label className="meal-slot-assign">
              <span className="muted">Assign dish</span>
            </label>
          )}
          <SegmentedControl
            className="segmented-control-full"
            ariaLabel="Dish role filter"
            value={roleFilter}
            options={mealLineRoleFilterOptions().map((value) => ({
              value,
              label: mealLineRoleFilterLabel(value),
            }))}
            disabled={actionDisabled}
            onChange={setRoleFilter}
          />
          <SearchSelect
            ariaLabel="Dish"
            value={dishId}
            options={dishOptions}
            disabled={actionDisabled}
            placeholder="Search dishes…"
            onChange={setDishId}
          />
          {dishId && recipesLoading ? (
            <p className="muted">Loading recipes…</p>
          ) : dishId && recipes.length > 1 ? (
            <SearchSelect
              ariaLabel="Recipe variant"
              value={recipeId}
              options={recipeOptions}
              disabled={actionDisabled}
              placeholder="Main recipe"
              emptyLabel="Main recipe"
              allowEmptyOption
              onChange={setRecipeId}
            />
          ) : dishId && recipes.length === 1 ? (
            <p className="muted meal-slot-recipe">
              Recipe: <strong>{recipes[0]?.variant_name}</strong>
              {recipes[0]?.is_main ? " (main)" : ""}
            </p>
          ) : null}
          {lines.length > 0 ? (
            <div className="row-between">
              <Button type="button" variant="ghost" size="sm" disabled={busy} onClick={() => setAddOpen(false)}>
                Cancel
              </Button>
              <Button type="button" size="sm" disabled={actionDisabled || !dishId} loading={busy} onClick={() => void submitDishSelection()}>
                Add dish
              </Button>
            </div>
          ) : (
            <Button type="button" disabled={actionDisabled || !dishId} loading={busy} onClick={() => void submitDishSelection()}>
              Add to meal
            </Button>
          )}
        </div>
      ) : null}

      {canModifyPlanning && lines.length > 0 && !addOpen ? (
        <Button type="button" variant="secondary" size="sm" disabled={actionDisabled} onClick={() => setAddOpen(true)}>
          + Add dish
        </Button>
      ) : null}

      {isFuture && canModifyPlanning ? (
        <Button type="button" variant="ghost" size="sm" disabled={actionDisabled} onClick={() => void handleDoNotPlan()}>
          Do not plan
        </Button>
      ) : null}
    </div>
  );
}
