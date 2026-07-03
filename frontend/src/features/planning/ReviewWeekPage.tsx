import { useCallback, useEffect, useMemo, useState } from "react";

import type { MealPlanItem } from "../../api/planning";
import { fetchMealHistory } from "../../api/planning";
import { useAuth } from "../auth/AuthContext";
import { MealSlotCard } from "./MealSlotCard";
import {
  filterReviewItems,
  formatPlanDate,
  groupItemsByDate,
  leftoverSourcesFor,
  needsReview,
  type ReviewFilter,
  weekDates,
} from "./planFormat";
import { useWeekPlan } from "./useWeekPlan";
import { WeekPlanShell, weekNavigationHandlers } from "./WeekPlanShell";

export function ReviewWeekPage() {
  const { accessToken } = useAuth();
  const { plan, dishes, error, loading, load, setPlan, setError } = useWeekPlan(accessToken);
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>("needs_review");
  const [sourceCandidates, setSourceCandidates] = useState<MealPlanItem[]>([]);
  const nav = weekNavigationHandlers(plan?.week_start_date ?? null, load);

  const loadSourceCandidates = useCallback(async () => {
    if (!accessToken || !plan) {
      setSourceCandidates([]);
      return;
    }
    const history = await fetchMealHistory(accessToken, 50);
    const byId = new Map<number, MealPlanItem>();
    for (const item of [...plan.items, ...history]) {
      byId.set(item.id, item);
    }
    setSourceCandidates(Array.from(byId.values()));
  }, [accessToken, plan]);

  useEffect(() => {
    void loadSourceCandidates().catch(() => setSourceCandidates(plan?.items ?? []));
  }, [loadSourceCandidates, plan?.items]);

  const visibleItems = useMemo(
    () => (plan ? filterReviewItems(plan.items, reviewFilter) : []),
    [plan, reviewFilter],
  );
  const grouped = useMemo(() => groupItemsByDate(visibleItems), [visibleItems]);
  const dates = useMemo(() => {
    if (!plan) {
      return [];
    }
    if (reviewFilter === "all") {
      return weekDates(plan.week_start_date);
    }
    const uniqueDates = [...new Set(visibleItems.map((item) => item.date))].sort();
    return uniqueDates;
  }, [plan, reviewFilter, visibleItems]);

  const needsReviewCount = useMemo(
    () => (plan ? plan.items.filter(needsReview).length : 0),
    [plan],
  );

  function replaceItem(updated: MealPlanItem) {
    setPlan((current) =>
      current
        ? { ...current, items: current.items.map((item) => (item.id === updated.id ? updated : item)) }
        : current,
    );
    setSourceCandidates((current) => {
      const byId = new Map(current.map((item) => [item.id, item]));
      byId.set(updated.id, updated);
      return Array.from(byId.values());
    });
  }

  if (loading && !plan) {
    return (
      <section className="card">
        <p className="muted">Loading review…</p>
      </section>
    );
  }

  return (
    <WeekPlanShell
      weekStart={plan?.week_start_date ?? null}
      loading={loading}
      title="Review meals"
      subtitle="Mark what was eaten, skipped, or eaten as leftovers."
      error={error}
      {...nav}
    >
      <section className="card stack">
        <div className="review-filter-bar">
          <div className="segmented-control" role="group" aria-label="Review filter">
            <button
              type="button"
              className={`segmented-control-option${reviewFilter === "needs_review" ? " segmented-control-option-active" : ""}`}
              onClick={() => setReviewFilter("needs_review")}
            >
              Needs review
              {needsReviewCount > 0 ? ` (${needsReviewCount})` : ""}
            </button>
            <button
              type="button"
              className={`segmented-control-option${reviewFilter === "all" ? " segmented-control-option-active" : ""}`}
              onClick={() => setReviewFilter("all")}
            >
              All meals
            </button>
          </div>
          {reviewFilter === "needs_review" && needsReviewCount === 0 ? (
            <p className="muted review-filter-empty">All meals reviewed for this week.</p>
          ) : null}
        </div>

        {visibleItems.length === 0 ? (
          <p className="muted">
            {reviewFilter === "needs_review"
              ? "Nothing needs review in this week."
              : "No meals in this week."}
            {reviewFilter === "needs_review" ? (
              <>
                {" "}
                <button type="button" className="button button-secondary" onClick={() => setReviewFilter("all")}>
                  Show all
                </button>
              </>
            ) : null}
          </p>
        ) : (
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
                        leftoverSources={leftoverSourcesFor(item, sourceCandidates)}
                        sourceLookupItems={sourceCandidates}
                        accessToken={accessToken!}
                        mode="review"
                        onChanged={replaceItem}
                        onError={setError}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </WeekPlanShell>
  );
}
