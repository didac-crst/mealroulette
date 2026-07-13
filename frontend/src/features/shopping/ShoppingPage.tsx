import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createShoppingList,
  fetchShoppingList,
  previewShoppingList,
  type ShoppingList,
  type ShoppingListItem,
  type ShoppingPlannedMeal,
  type ShoppingQuantityComponent,
  type ShoppingSourceContribution,
  updateShoppingListItem,
} from "../../api/shopping";
import { Button, Card, EmptyState, PageHeader, PageLoadingState } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { formatPlanDate, todayIso } from "../planning/planFormat";

const DAY_PRESETS = [1, 2, 3, 7] as const;

function formatQuantity(value: string): string {
  const number = Number(value);
  if (Number.isFinite(number) && Number.isInteger(number)) {
    return String(number);
  }
  return value;
}

function groupByCategory(items: ShoppingListItem[]): Map<string, ShoppingListItem[]> {
  const grouped = new Map<string, ShoppingListItem[]>();
  for (const item of items) {
    const list = grouped.get(item.category) ?? [];
    list.push(item);
    grouped.set(item.category, list);
  }
  return new Map([...grouped.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

function formatSlotLabel(mealSlot: ShoppingPlannedMeal["meal_slot"]): string {
  return mealSlot === "lunch" ? "Lunch" : "Dinner";
}

function formatContributionLabel(contribution: ShoppingSourceContribution): string {
  const slot = formatSlotLabel(contribution.meal_slot);
  const recipe = contribution.recipe_variant_name ? ` (${contribution.recipe_variant_name})` : "";
  const optional = contribution.optional ? " · optional" : "";
  return `${formatPlanDate(contribution.date)} ${slot}: ${contribution.dish_name}${recipe} — ${formatQuantity(contribution.quantity)} ${contribution.unit_symbol}${optional}`;
}

function formatPlannedMealLabel(meal: ShoppingPlannedMeal): string {
  const recipe = meal.recipe_variant_name ? ` (${meal.recipe_variant_name})` : "";
  return `${formatPlanDate(meal.date)} ${formatSlotLabel(meal.meal_slot)}: ${meal.dish_name}${recipe}`;
}

function formatIncludesLine(components: ShoppingQuantityComponent[]): string | null {
  if (components.length <= 1) {
    return null;
  }
  return components
    .map((component) => `${formatQuantity(component.quantity)} ${component.unit_symbol}`)
    .join(" + ");
}

export function ShoppingPage() {
  const { accessToken } = useAuth();
  const [days, setDays] = useState<number>(3);
  const [excludePantry, setExcludePantry] = useState(true);
  const [list, setList] = useState<ShoppingList | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fromDate = todayIso();

  const loadPreview = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const preview = await previewShoppingList(accessToken, {
        from: fromDate,
        days,
        exclude_pantry: excludePantry,
      });
      return preview;
    } catch (err) {
      throw err instanceof Error ? err : new Error("Failed to load shopping list");
    }
  }, [accessToken, days, excludePantry, fromDate]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    void loadPreview()
      .then((preview) => {
        if (!cancelled && preview) {
          setList(preview);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load shopping list");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, loadPreview]);

  const grouped = useMemo(() => groupByCategory(list?.items ?? []), [list]);

  const replaceItem = (updated: ShoppingListItem) => {
    setList((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        items: current.items.map((item) => (item.id === updated.id ? updated : item)),
      };
    });
  };

  const handleSave = async () => {
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const saved = await createShoppingList(accessToken, {
        from_date: fromDate,
        days,
        exclude_pantry: excludePantry,
      });
      setList(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save shopping list");
    } finally {
      setSaving(false);
    }
  };

  const handleReloadSaved = async () => {
    if (!accessToken || !list?.id) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const saved = await fetchShoppingList(accessToken, list.id);
      setList(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reload shopping list");
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (item: ShoppingListItem, checked: boolean) => {
    if (!accessToken || item.id == null) {
      return;
    }
    try {
      const updated = await updateShoppingListItem(accessToken, item.id, { checked });
      replaceItem(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update item");
    }
  };

  const isSaved = list?.id != null;
  const items = list?.items ?? [];
  const checkedCount = items.filter((item) => item.checked).length;
  const totalCount = items.length;

  if (loading && !list) {
    return <PageLoadingState message="Loading shopping list…" />;
  }

  return (
    <div className="stack shopping-page">
      <Card density="comfortable" className="stack">
        <PageHeader
          title="Shopping"
          subtitle={`Ingredients for planned meals from ${formatPlanDate(fromDate)}${
            list ? ` through ${formatPlanDate(list.to_date)}` : ""
          }.`}
          actions={
            !isSaved ? (
              <Button type="button" disabled={saving || loading} loading={saving} onClick={() => void handleSave()}>
                Save list
              </Button>
            ) : (
              <Button type="button" variant="secondary" disabled={loading} onClick={() => void handleReloadSaved()}>
                Refresh
              </Button>
            )
          }
        />

        <div className="shopping-controls">
          <div className="shopping-presets" role="group" aria-label="Shopping window">
            {DAY_PRESETS.map((preset) => (
              <button
                key={preset}
                type="button"
                className={`button button-secondary${days === preset ? " shopping-preset-active" : ""}`}
                onClick={() => setDays(preset)}
              >
                {preset} day{preset === 1 ? "" : "s"}
              </button>
            ))}
          </div>
          <label className="shopping-toggle">
            <input
              type="checkbox"
              checked={excludePantry}
              onChange={(event) => setExcludePantry(event.target.checked)}
            />
            Exclude pantry items
          </label>
        </div>

        {error ? <p className="error-text">{error}</p> : null}
      </Card>

      {list && totalCount > 0 ? (
        <p className="shopping-progress-bar" role="status">
          {checkedCount} of {totalCount} completed
        </p>
      ) : null}

      {list && list.planned_meals.length > 0 ? (
        <Card density="comfortable" className="stack">
          <h3>Planned meals in window</h3>
          <ul className="shopping-planned-meals bulleted-list">
            {list.planned_meals.map((meal) => (
              <li key={meal.meal_plan_item_id}>{formatPlannedMealLabel(meal)}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      {list && list.items.length === 0 ? (
        <Card density="comfortable">
          <EmptyState
            title="Everything is covered"
            description="No planned meals with recipes in this window, or all slots are empty or skipped."
          />
        </Card>
      ) : null}

      {[...grouped.entries()].map(([category, categoryItems]) => (
        <Card key={category} density="comfortable" className="stack">
          <h3 className="shopping-category">{category}</h3>
          <ul className="shopping-items">
            {categoryItems.map((item) => {
              const includesLine = item.approximate ? formatIncludesLine(item.raw_components) : null;
              return (
                <li key={`${item.ingredient_id}-${item.unit_id}-${item.quantity}`} className="shopping-item">
                  <label className="shopping-item-label">
                    {isSaved && item.id != null ? (
                      <input
                        type="checkbox"
                        checked={item.checked}
                        onChange={(event) => void handleToggle(item, event.target.checked)}
                      />
                    ) : null}
                    <span className={item.checked ? "shopping-item-checked" : undefined}>
                      <strong>
                        {item.approximate ? "~" : ""}
                        {formatQuantity(item.quantity)} {item.unit_symbol}
                      </strong>{" "}
                      {item.display_name}
                      {item.optional ? <span className="muted"> (optional)</span> : null}
                    </span>
                  </label>
                  {includesLine ? <p className="muted shopping-item-detail">includes: {includesLine}</p> : null}
                  {item.source_contributions.length > 0 ? (
                    <ul className="shopping-item-breakdown bulleted-list">
                      {item.source_contributions.map((contribution) => (
                        <li key={`${contribution.meal_plan_item_id}-${contribution.quantity}-${contribution.unit_symbol}`}>
                          {formatContributionLabel(contribution)}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </Card>
      ))}
    </div>
  );
}
