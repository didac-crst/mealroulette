import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { fetchCurrentMealPlan } from "../../api/planning";

import { needsReview } from "./planFormat";

export function useReviewAttentionCount(accessToken: string | null): boolean {
  const location = useLocation();
  const [hasAttention, setHasAttention] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      setHasAttention(false);
      return;
    }

    let cancelled = false;
    fetchCurrentMealPlan(accessToken)
      .then((plan) => {
        if (!cancelled) {
          setHasAttention(plan.items.some(needsReview));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHasAttention(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken, location.pathname]);

  return hasAttention;
}
