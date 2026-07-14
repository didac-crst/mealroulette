import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchIngredientCategories } from "../../api/catalog";
import {
  createShoppingList,
  fetchShoppingList,
  previewShoppingList,
  updateShoppingListItem,
  type ShoppingList,
  type ShoppingListItem,
  type ShoppingPlannedMeal,
} from "../../api/shopping";
import {
  Button,
  Card,
  DisclosureSection,
  EmptyState,
  PageShell,
  SegmentedControl,
  Switch,
} from "../../components/ui";
import { formatShoppingCategory } from "../../lib/formatShoppingCategory";
import { useAuth } from "../auth/AuthContext";
import { formatPlanDate, todayIso } from "../planning/planFormat";
import { ShoppingListItemRow } from "./ShoppingListItemRow";

const DAY_PRESETS = [1, 2, 3, 7] as const;

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

function formatPlannedMealLabel(meal: ShoppingPlannedMeal): string {
  const recipe = meal.recipe_variant_name ? ` (${meal.recipe_variant_name})` : "";
  return `${formatPlanDate(meal.date)} ${formatSlotLabel(meal.meal_slot)}: ${meal.dish_name}${recipe}`;
}

export function ShoppingPage() {
  const { accessToken } = useAuth();
  const [days, setDays] = useState<number>(3);
  const [excludePantry, setExcludePantry] = useState(true);
  const [list, setList] = useState<ShoppingList | null>(null);
  const [categoryLabels, setCategoryLabels] = useState<Map<string, string>>(new Map());
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

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    fetchIngredientCategories(accessToken)
      .then((categories) => {
        if (!cancelled) {
          setCategoryLabels(new Map(categories.map((category) => [category.id, category.label])));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCategoryLabels(new Map());
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

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
  const dayOptions = DAY_PRESETS.map((preset) => ({
    value: preset,
    label: `${preset} day${preset === 1 ? "" : "s"}`,
  }));
  const windowSummary = `${formatPlanDate(fromDate)}${
    list ? ` through ${formatPlanDate(list.to_date)}` : ""
  }`;

  return (
    <div className="stack shopping-page">
      <PageShell
        title="Shopping"
        subtitle={`Ingredients for planned meals from ${windowSummary}.`}
        loading={loading && !list}
        loadingMessage="Loading shopping list…"
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
      {error ? (
        <p className="error-text week-shell-error" role="alert">
          {error}
        </p>
      ) : null}

      {list && totalCount > 0 ? (
        <p className="shopping-progress-bar" role="status">
          {checkedCount} of {totalCount} completed
        </p>
      ) : null}

      {list && list.items.length === 0 ? (
        <Card density="comfortable">
          <EmptyState
            title="Everything is covered"
            description="No planned meals with recipes in this window, or all slots are empty or skipped."
          />
        </Card>
      ) : null}

      <div className="shopping-checklist">
        {[...grouped.entries()].map(([category, categoryItems]) => (
          <Card key={category} density="comfortable" className="stack shopping-category-card">
            <h2 className="shopping-category">{formatShoppingCategory(category, categoryLabels)}</h2>
            <div className="shopping-list-rows">
              {categoryItems.map((item) => (
                <ShoppingListItemRow
                  key={`${item.ingredient_id}-${item.unit_id}-${item.quantity}`}
                  item={item}
                  showCheckbox={isSaved}
                  onToggle={(checked) => void handleToggle(item, checked)}
                />
              ))}
            </div>
          </Card>
        ))}
      </div>

      {list ? (
        <div className="shopping-secondary-panels">
          {list.planned_meals.length > 0 ? (
            <Card density="comfortable">
              <DisclosureSection
                title="Planned meals in window"
                meta={`${list.planned_meals.length}`}
              >
                <ul className="shopping-planned-meals bulleted-list">
                  {list.planned_meals.map((meal) => (
                    <li key={meal.meal_plan_item_id}>{formatPlannedMealLabel(meal)}</li>
                  ))}
                </ul>
              </DisclosureSection>
            </Card>
          ) : null}

          <Card density="comfortable">
            <DisclosureSection title="List options">
              <div className="shopping-controls-panel">
                <SegmentedControl
                  className="segmented-control-full"
                  ariaLabel="Shopping window"
                  value={days}
                  options={dayOptions}
                  onChange={setDays}
                />
                <div className="shopping-options-row">
                  <Switch
                    checked={excludePantry}
                    onChange={(event) => setExcludePantry(event.target.checked)}
                    label="Exclude pantry items"
                  />
                </div>
                <p className="muted shopping-options-hint">Window: {windowSummary}</p>
              </div>
            </DisclosureSection>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
