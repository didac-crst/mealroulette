import { useCallback, useEffect, useRef, useState } from "react";

import { fetchDishes } from "../../api/catalog";
import { ApiError } from "../../api/client";
import {
  fetchCurrentMealPlan,
  fetchMealPlanByWeek,
  type MealPlan,
  type MealPlanItem,
} from "../../api/planning";

export function useWeekPlan(accessToken: string | null) {
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [dishes, setDishes] = useState<Awaited<ReturnType<typeof fetchDishes>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!accessToken) {
      setDishes([]);
      return;
    }
    let cancelled = false;
    fetchDishes(accessToken)
      .then((dishData) => {
        if (!cancelled) {
          setDishes(dishData);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDishes([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const load = useCallback(
    async (targetWeekStart?: string) => {
      if (!accessToken) {
        setLoading(false);
        return;
      }
      const requestId = ++requestIdRef.current;
      setLoading(true);
      setError(null);
      try {
        const planData = targetWeekStart
          ? await fetchMealPlanByWeek(accessToken, targetWeekStart)
          : await fetchCurrentMealPlan(accessToken);
        if (requestId !== requestIdRef.current) {
          return;
        }
        setPlan(planData);
      } catch (err) {
        if (requestId !== requestIdRef.current) {
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load meal plan");
      } finally {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [accessToken],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const replaceItem = useCallback((updated: MealPlanItem) => {
    setPlan((current) =>
      current
        ? { ...current, items: current.items.map((item) => (item.id === updated.id ? updated : item)) }
        : current,
    );
  }, []);

  const replaceItems = useCallback((updated: MealPlanItem[]) => {
    const byId = new Map(updated.map((item) => [item.id, item]));
    setPlan((current) =>
      current
        ? {
            ...current,
            items: current.items.map((item) => byId.get(item.id) ?? item),
          }
        : current,
    );
  }, []);

  return { plan, dishes, error, loading, load, setPlan, setError, replaceItem, replaceItems };
}
