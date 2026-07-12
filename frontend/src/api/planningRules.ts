import { apiRequest } from "./client";

export type WeeklyTargetSpec = {
  min: number;
  max: number;
};

export type PlanningRulesConfig = {
  weekly_targets: Record<string, WeeklyTargetSpec>;
  weekly_target_tolerance: number;
  avoid_same_dish_within_days: number;
  avoid_similar_meals_within_days: number;
  similarity_threshold: number;
  prefer_seasonal: boolean;
  prefer_high_rated: boolean;
  allow_leftovers: boolean;
  default_grams_per_count: number;
  vector_min_grams: number;
  plan_attempts: number;
  history_window_days: number;
};

export type PlanningRule = {
  id: number;
  name: string;
  active: boolean;
  rules: PlanningRulesConfig;
  created_at: string;
  updated_at: string;
};

export function fetchActivePlanningRules(token: string): Promise<PlanningRule> {
  return apiRequest<PlanningRule>("/api/planning-rules/active", { token });
}

export function updateActivePlanningRules(
  token: string,
  rules: PlanningRulesConfig,
): Promise<PlanningRule> {
  return apiRequest<PlanningRule>("/api/planning-rules/active", {
    method: "PUT",
    token,
    body: JSON.stringify({ rules }),
  });
}
