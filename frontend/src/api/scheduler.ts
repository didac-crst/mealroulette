import { apiRequest } from "./client";

export type SchedulerSettings = {
  enabled: boolean;
  run_weekday: number;
  run_time: string;
  timezone: string;
  target_week_offset: number;
  notify_telegram: boolean;
  notify_planning_days: number;
  last_roulette_at: string | null;
  last_error: string | null;
};

export type SchedulerSettingsInput = {
  enabled?: boolean;
  run_weekday?: number;
  run_time?: string;
  timezone?: string;
  target_week_offset?: number;
  notify_telegram?: boolean;
  notify_planning_days?: number;
};

export type SchedulerRouletteRunResult = {
  ran: boolean;
  detail: string;
  meal_plan_id: number | null;
  week_start_date: string | null;
  assignments_count: number;
  warnings: string[];
  telegram_recipient_count: number;
};

const WEEKDAY_LABELS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

export function schedulerWeekdayLabel(weekday: number): string {
  return WEEKDAY_LABELS[weekday] ?? `Day ${weekday}`;
}

export function fetchSchedulerSettings(token: string): Promise<SchedulerSettings> {
  return apiRequest<SchedulerSettings>("/api/scheduler/settings", { token });
}

export function updateSchedulerSettings(
  token: string,
  payload: SchedulerSettingsInput,
): Promise<SchedulerSettings> {
  return apiRequest<SchedulerSettings>("/api/scheduler/settings", {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

export function runSchedulerRouletteNow(token: string): Promise<SchedulerRouletteRunResult> {
  return apiRequest<SchedulerRouletteRunResult>("/api/scheduler/run-roulette", {
    method: "POST",
    token,
  });
}
