import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { MealPlanItem } from "../../api/planning";
import { fetchMealHistory } from "../../api/planning";
import { Button, Card, EmptyState, PageLoadingState } from "../../components/ui";
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
  const { plan, dishes, error, loading, load, setError, replaceItem } = useWeekPlan(accessToken);
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>("needs_review");
  const [sourceCandidates, setSourceCandidates] = useState<MealPlanItem[]>([]);
  const sourceRequestIdRef = useRef(0);
  const nav = weekNavigationHandlers(plan?.week_start_date ?? null, load);

  const loadSourceCandidates = useCallback(async () => {
    if (!accessToken || !plan) {
      setSourceCandidates([]);
      return;
    }
    const requestId = ++sourceRequestIdRef.current;
    const history = await fetchMealHistory(accessToken, 50);
    if (requestId !== sourceRequestIdRef.current) {
      return;
    }
    const byId = new Map<number, MealPlanItem>();
    for (const item of [...plan.items, ...history]) {
      byId.set(item.id, item);
    }
    setSourceCandidates(Array.from(byId.values()));
  }, [accessToken, plan]);

  useEffect(() => {
    let cancelled = false;
    loadSourceCandidates().catch(() => {
      if (!cancelled) {
        setSourceCandidates(plan?.items ?? []);
      }
    });
    return () => {
      cancelled = true;
      sourceRequestIdRef.current += 1;
    };
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

  const reviewSubtitle =
    needsReviewCount > 0
      ? `${needsReviewCount} meal${needsReviewCount === 1 ? "" : "s"} need review`
      : "You are up to date";

  function handleItemChanged(updated: MealPlanItem) {
    replaceItem(updated);
    setSourceCandidates((current) => {
      const byId = new Map(current.map((item) => [item.id, item]));
      byId.set(updated.id, updated);
      return Array.from(byId.values());
    });
  }

  if (loading && !plan) {
    return <PageLoadingState message="Loading review…" />;
  }

  return (
    <WeekPlanShell
      weekStart={plan?.week_start_date ?? null}
      loading={loading}
      title="Review"
      subtitle={`Mark what was eaten, skipped, or eaten as leftovers. · ${reviewSubtitle}`}
      error={error}
      className="review-page"
      {...nav}
    >
      <Card density="comfortable" className="stack">
        <div className="review-filter-bar">
          <div className="segmented-control" role="group" aria-label="Review filter">
            <button
              type="button"
              className={`segmented-control-option${reviewFilter === "needs_review" ? " segmented-control-option-active" : ""}`}
              aria-pressed={reviewFilter === "needs_review"}
              onClick={() => setReviewFilter("needs_review")}
            >
              Needs review
              {needsReviewCount > 0 ? ` (${needsReviewCount})` : ""}
            </button>
            <button
              type="button"
              className={`segmented-control-option${reviewFilter === "all" ? " segmented-control-option-active" : ""}`}
              aria-pressed={reviewFilter === "all"}
              onClick={() => setReviewFilter("all")}
            >
              All meals
            </button>
          </div>
        </div>

        {visibleItems.length === 0 ? (
          <EmptyState
            title={
              reviewFilter === "needs_review"
                ? "You are up to date"
                : "No meals in this week"
            }
            description={
              reviewFilter === "needs_review"
                ? "No meals need review for this week."
                : "There are no meals in the selected week."
            }
            action={
              reviewFilter === "needs_review" ? (
                <Button type="button" variant="secondary" onClick={() => setReviewFilter("all")}>
                  Show all meals
                </Button>
              ) : undefined
            }
          />
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
                        onChanged={handleItemChanged}
                        onError={setError}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </WeekPlanShell>
  );
}
