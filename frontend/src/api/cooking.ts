import { apiRequest } from "./client";

export type CookingTimerAlert = {
  id: number;
  recipe_id: number;
  recipe_step_id: number;
  step_number: number;
  dish_name: string;
  recipe_name: string;
  fire_at: string;
  status: string;
  telegram_scheduled: boolean;
};

export type CookingTimerAlertInput = {
  recipe_id: number;
  recipe_step_id: number;
  step_number: number;
  remaining_seconds: number;
};

export async function scheduleCookingTimerAlert(
  token: string,
  payload: CookingTimerAlertInput,
): Promise<CookingTimerAlert> {
  return apiRequest<CookingTimerAlert>("/api/cooking-timer-alerts", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function cancelCookingTimerAlert(token: string, alertId: number): Promise<{ cancelled: boolean }> {
  return apiRequest<{ cancelled: boolean }>(`/api/cooking-timer-alerts/${alertId}`, {
    method: "DELETE",
    token,
  });
}

export async function cancelCookingTimerAlertForStep(
  token: string,
  recipeStepId: number,
): Promise<{ cancelled: boolean }> {
  return apiRequest<{ cancelled: boolean }>(`/api/cooking-timer-alerts/by-step/${recipeStepId}`, {
    method: "DELETE",
    token,
  });
}
