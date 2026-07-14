import { useMemo, useState } from "react";

import { ApiError } from "../../api/client";
import {
  generateMealPlanWeekDetails,
  rerollMealPlanItem,
  startOverMealPlanReroll,
  swapMealPlanItems,
  undoMealPlanRoulette,
  type MealPlanItem,
  type MealPlanRouletteResponse,
} from "../../api/planning";
import { Button, Card, PageLoadingState } from "../../components/ui";
import { MealSlotCard } from "./MealSlotCard";
import { formatPlanDate, groupItemsByDate, weekDates } from "./planFormat";
import { useWeekPlan } from "./useWeekPlan";
import { WeekPlanShell, weekNavigationHandlers } from "./WeekPlanShell";
import { useAuth } from "../auth/AuthContext";

export function PlanWeekPage() {
  const { accessToken } = useAuth();
  const { plan, dishes, error, loading, load, setError, replaceItem, replaceItems } = useWeekPlan(accessToken);
  const nav = weekNavigationHandlers(plan?.week_start_date ?? null, load);
  const [rouletteBusy, setRouletteBusy] = useState(false);
  const [lastRoulette, setLastRoulette] = useState<MealPlanRouletteResponse | null>(null);
  const [rerollExhaustedByItemId, setRerollExhaustedByItemId] = useState<Record<number, string>>({});

  const grouped = useMemo(
    (): Map<string, MealPlanItem[]> => (plan ? groupItemsByDate(plan.items) : new Map()),
    [plan],
  );
  const dates = useMemo(() => (plan ? weekDates(plan.week_start_date) : []), [plan]);

  async function handleGenerateWeek() {
    if (!accessToken || !plan) {
      return;
    }
    setRouletteBusy(true);
    setError(null);
    try {
      const details = await generateMealPlanWeekDetails(accessToken, plan.id);
      setLastRoulette(details);
      await load(plan.week_start_date);
    } catch (err) {
      setLastRoulette(null);
      setError(err instanceof ApiError ? err.message : "Failed to generate week");
    } finally {
      setRouletteBusy(false);
    }
  }

  async function handleUndoRoulette() {
    if (!accessToken || !plan) {
      return;
    }
    setRouletteBusy(true);
    setError(null);
    try {
      await undoMealPlanRoulette(accessToken, plan.id);
      setLastRoulette(null);
      await load(plan.week_start_date);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to undo roulette");
    } finally {
      setRouletteBusy(false);
    }
  }

  async function handleReroll(item: MealPlanItem) {
    if (!accessToken || !plan) {
      return;
    }
    setRouletteBusy(true);
    setError(null);
    try {
      const result = await rerollMealPlanItem(accessToken, item.id);
      if (result.status === "exhausted") {
        setRerollExhaustedByItemId((current) => ({
          ...current,
          [item.id]: result.message ?? "You've seen all suitable alternatives.",
        }));
        return;
      }
      setRerollExhaustedByItemId((current) => {
        const next = { ...current };
        delete next[item.id];
        return next;
      });
      replaceItem(result.item);
      setLastRoulette(null);
      await load(plan.week_start_date);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to reroll meal");
    } finally {
      setRouletteBusy(false);
    }
  }

  async function handleStartOverReroll(item: MealPlanItem) {
    if (!accessToken || !plan) {
      return;
    }
    setRouletteBusy(true);
    setError(null);
    try {
      await startOverMealPlanReroll(accessToken, item.id);
      setRerollExhaustedByItemId((current) => {
        const next = { ...current };
        delete next[item.id];
        return next;
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to reset reroll history");
    } finally {
      setRouletteBusy(false);
    }
  }

  async function handleSwap(source: MealPlanItem, targetItemId: number) {
    if (!accessToken) {
      return;
    }
    setRouletteBusy(true);
    setError(null);
    try {
      const result = await swapMealPlanItems(accessToken, source.id, targetItemId);
      replaceItems([result.source, result.target]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to swap meals");
    } finally {
      setRouletteBusy(false);
    }
  }

  if (loading && !plan) {
    return <PageLoadingState message="Loading week plan…" />;
  }

  return (
    <WeekPlanShell
      weekStart={plan?.week_start_date ?? null}
      loading={loading || rouletteBusy}
      title="Plan"
      subtitle="Assign dishes, run roulette, lock meals, and swap slots."
      error={error}
      {...nav}
    >
      <Card density="comfortable" className="stack plan-roulette-toolbar">
        <div className="row-between plan-roulette-actions">
          <div>
            <h3 className="section-title">Meal roulette</h3>
            <p className="muted">Fill open slots automatically. Locked meals stay as they are.</p>
          </div>
          <div className="row-actions">
            <Button
              type="button"
              variant="roulette"
              disabled={!plan || rouletteBusy}
              loading={rouletteBusy}
              onClick={() => void handleGenerateWeek()}
            >
              Generate week
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={!plan?.roulette_undo_available || rouletteBusy}
              onClick={() => void handleUndoRoulette()}
            >
              Undo roulette
            </Button>
          </div>
        </div>
        {lastRoulette && lastRoulette.warnings.length > 0 ? (
          <div className="roulette-warnings">
            {lastRoulette.warnings.map((warning) => (
              <p key={warning} className="muted">
                {warning}
              </p>
            ))}
          </div>
        ) : null}
        {lastRoulette && lastRoulette.variety.items.length > 0 ? (
          <div className="roulette-variety stack">
            <p className="muted">
              Variety vs neighbours (avg distance{" "}
              {lastRoulette.variety.average_distance_to_neighbours?.toFixed(2) ?? "—"})
            </p>
            <ul className="variety-list">
              {lastRoulette.variety.items.map((entry) => (
                <li key={entry.item_id ?? entry.dish_id}>
                  <strong>{entry.dish_name}</strong>
                  <span className="muted">
                    {" "}
                    · {entry.variety_label}
                    {entry.nearest_neighbour_dish
                      ? ` (nearest: ${entry.nearest_neighbour_dish})`
                      : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Card>

      <Card density="comfortable" className="stack">
        <div className="meal-week-grid">
          {dates.map((date) => {
            const dayItems = grouped.get(date) ?? [];
            return (
              <div key={date} className="meal-week-day">
                <h4 className="meal-day-heading">{formatPlanDate(date)}</h4>
                <div className="stack">
                  {dayItems.map((item) => (
                    <MealSlotCard
                      key={item.id}
                      item={item}
                      dishes={dishes}
                      planItems={plan?.items ?? []}
                      leftoverSources={[]}
                      accessToken={accessToken!}
                      mode="plan"
                      rouletteBusy={rouletteBusy}
                      onChanged={replaceItem}
                      onError={setError}
                      onReroll={handleReroll}
                      onStartOverReroll={handleStartOverReroll}
                      rerollExhaustedMessage={rerollExhaustedByItemId[item.id]}
                      onSwap={handleSwap}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </WeekPlanShell>
  );
}
