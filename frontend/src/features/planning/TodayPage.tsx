import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { fetchSchedulerSettings } from "../../api/scheduler";
import { fetchMealHistory, type MealPlanItem } from "../../api/planning";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, Card, EmptyState, PageShell } from "../../components/ui";
import { todayIsoInTimeZone } from "../../lib/datetime";
import { useAuth } from "../auth/AuthContext";
import { TodayMealCard } from "./TodayMealCard";
import { countNeedsReviewForDate, formatPlanDate, formatSlotLabel, todayMealSlots } from "./planFormat";
import { useWeekPlan } from "./useWeekPlan";

const DEFAULT_TIMEZONE = "Europe/Paris";

function TodayEmptySlot({ mealSlot }: { mealSlot: "lunch" | "dinner" }) {
  return (
    <Card as="article" density="comfortable" className="today-empty-slot">
      <p className="meal-slot-label">{formatSlotLabel(mealSlot)}</p>
      <p className="muted">Nothing planned</p>
    </Card>
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

  const subtitleParts = [formatPlanDate(today)];
  if (needsReviewCount > 0) {
    subtitleParts.push(
      `${needsReviewCount} meal${needsReviewCount === 1 ? "" : "s"} need review`,
    );
  } else if (hasAnyMeals) {
    subtitleParts.push("All meals reviewed for today");
  }

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

  return (
    <section className="stack today-page">
      <PageShell
        title="Today"
        subtitle={subtitleParts.join(" · ")}
        loading={loading && !plan}
        loadingMessage="Loading today…"
      >
      {error ? (
        <Card density="comfortable">
          <p className="error" role="alert">
            {error}
          </p>
          <Button type="button" variant="secondary" onClick={() => void load()}>
            Retry
          </Button>
        </Card>
      ) : null}

      {!hasAnyMeals ? (
        <Card density="comfortable">
          <EmptyState
            title="Nothing planned yet"
            description="Choose a dish on the plan or spin the roulette for the week."
            action={<ButtonLink to="/plan">Plan this week</ButtonLink>}
          />
        </Card>
      ) : (
        <div className="today-meal-grid">
          {slots.map(({ meal_slot, item }) =>
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
          )}
        </div>
      )}

      <div className="today-footer-links">
        <Link to="/review">View full week</Link>
        <Link to="/plan">Plan week</Link>
      </div>
      </PageShell>
    </section>
  );
}
