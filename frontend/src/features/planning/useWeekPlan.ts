import { useCallback, useEffect, useState } from "react";

import { fetchDishes } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { fetchCurrentMealPlan, fetchMealPlanByWeek, type MealPlan } from "../../api/planning";

export function useWeekPlan(accessToken: string | null) {
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [dishes, setDishes] = useState<Awaited<ReturnType<typeof fetchDishes>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (targetWeekStart?: string) => {
      if (!accessToken) {
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const [planData, dishData] = await Promise.all([
          targetWeekStart
            ? fetchMealPlanByWeek(accessToken, targetWeekStart)
            : fetchCurrentMealPlan(accessToken),
          fetchDishes(accessToken),
        ]);
        setPlan(planData);
        setDishes(dishData);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load meal plan");
      } finally {
        setLoading(false);
      }
    },
    [accessToken],
  );

  useEffect(() => {
    void load();
  }, [load]);

  return { plan, dishes, error, loading, load, setPlan, setError };
}
