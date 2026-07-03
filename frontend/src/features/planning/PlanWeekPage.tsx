import { useMemo } from "react";

import type { MealPlanItem } from "../../api/planning";
import { useAuth } from "../auth/AuthContext";
import { MealSlotCard } from "./MealSlotCard";
import { formatPlanDate, groupItemsByDate, weekDates } from "./planFormat";
import { useWeekPlan } from "./useWeekPlan";
import { WeekPlanShell, weekNavigationHandlers } from "./WeekPlanShell";

export function PlanWeekPage() {
  const { accessToken } = useAuth();
  const { plan, dishes, error, loading, load, setPlan, setError } = useWeekPlan(accessToken);
  const nav = weekNavigationHandlers(plan?.week_start_date ?? null, load);

  const grouped = useMemo(
    (): Map<string, MealPlanItem[]> => (plan ? groupItemsByDate(plan.items) : new Map()),
    [plan],
  );
  const dates = useMemo(() => (plan ? weekDates(plan.week_start_date) : []), [plan]);

  function replaceItem(updated: MealPlanItem) {
    setPlan((current) =>
      current
        ? { ...current, items: current.items.map((item) => (item.id === updated.id ? updated : item)) }
        : current,
    );
  }

  if (loading && !plan) {
    return (
      <section className="card">
        <p className="muted">Loading week plan…</p>
      </section>
    );
  }

  return (
    <WeekPlanShell
      weekStart={plan?.week_start_date ?? null}
      loading={loading}
      title="Plan week"
      subtitle="Assign dishes, choose recipe variants, and lock meals."
      error={error}
      {...nav}
    >
      <section className="card stack">
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
                        leftoverSources={[]}
                      accessToken={accessToken!}
                      mode="plan"
                      onChanged={replaceItem}
                      onError={setError}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </WeekPlanShell>
  );
}
