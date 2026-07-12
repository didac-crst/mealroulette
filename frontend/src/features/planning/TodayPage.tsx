import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { fetchSchedulerSettings } from "../../api/scheduler";
import { fetchMealHistory, type MealPlanItem } from "../../api/planning";
import { todayIsoInTimeZone } from "../../lib/datetime";
import { ButtonLink } from "../../components/ButtonLink";
import { useAuth } from "../auth/AuthContext";
import { TodayMealCard } from "./TodayMealCard";
import { countNeedsReviewForDate, formatPlanDate, formatSlotLabel, todayMealSlots } from "./planFormat";
import { useWeekPlan } from "./useWeekPlan";

const DEFAULT_TIMEZONE = "Europe/Paris";

function TodayEmptySlot({ mealSlot }: { mealSlot: "lunch" | "dinner" }) {
  return (
    <article className="meal-slot-card today-empty-slot">
      <p className="meal-slot-label">{formatSlotLabel(mealSlot)}</p>
      <p className="muted">Nothing planned</p>
    </article>
  );
}

export function TodayPage() {
  const { accessToken } = useAuth();
  const { plan, dishes, error, loading, load, setError, replaceItem } = useWeekPlan(accessToken);
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [sourceCandidates, setSourceCandidates] = useState<MealPlanItem[]>([]);
  const sourceRequestIdRef = useRef(0);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    fetchSchedulerSettings(accessToken)
      .then((settings) => {
        if (!cancelled) {
          setTimezone(settings.timezone);
        }
      })
      .catch(() => {
        // Keep default timezone when settings cannot be loaded.
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const today = todayIsoInTimeZone(timezone);
  const slots = useMemo(() => (plan ? todayMealSlots(plan.items, today) : []), [plan, today]);
  const needsReviewCount = useMemo(
    () => (plan ? countNeedsReviewForDate(plan.items, today) : 0),
    [plan, today],
  );
  const hasAnyMeals = slots.some((slot) => slot.item != null);

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

  function handleItemChanged(updated: MealPlanItem) {
    replaceItem(updated);
    setSourceCandidates((current) => {
      const byId = new Map(current.map((item) => [item.id, item]));
      byId.set(updated.id, updated);
      return Array.from(byId.values());
    });
  }

  if (loading && !plan) {
    return (
      <section className="card">
        <p className="muted">Loading today…</p>
      </section>
    );
  }

  return (
    <section className="stack today-page">
      <header className="card stack today-header">
        <div>
          <h2>Today</h2>
          <p className="muted">{formatPlanDate(today)}</p>
          {needsReviewCount > 0 ? (
            <p className="muted">
              {needsReviewCount} meal{needsReviewCount === 1 ? "" : "s"} need review
            </p>
          ) : hasAnyMeals ? (
            <p className="muted">All meals reviewed for today</p>
          ) : null}
        </div>
      </header>

      {error ? (
        <section className="card">
          <p className="error" role="alert">
            {error}
          </p>
          <button type="button" className="button button-secondary" onClick={() => void load()}>
            Retry
          </button>
        </section>
      ) : null}

      {!hasAnyMeals ? (
        <section className="card stack today-empty-day">
          <p className="muted">No meals planned for today.</p>
          <ButtonLink to="/plan">Plan this week</ButtonLink>
        </section>
      ) : (
        slots.map(({ meal_slot, item }) =>
          item ? (
            <TodayMealCard
              key={item.id}
              item={item}
              dishes={dishes}
              planItems={plan?.items ?? []}
              leftoverSources={sourceCandidates}
              sourceLookupItems={sourceCandidates}
              accessToken={accessToken ?? ""}
              onChanged={handleItemChanged}
              onError={setError}
            />
          ) : (
            <TodayEmptySlot key={meal_slot} mealSlot={meal_slot} />
          ),
        )
      )}

      <div className="today-footer-links">
        <Link to="/review">View full week</Link>
        <Link to="/plan">Plan week</Link>
      </div>
    </section>
  );
}
