import { apiRequest } from "./client";

export type TelegramSubscriber = {
  id: string;
  chat_id: string;
  telegram_user_id: string | null;
  username: string | null;
  display_name: string | null;
  subscribed_at: string;
};

export type TelegramSettings = {
  enabled: boolean;
  has_bot_token: boolean;
  subscriber_count: number;
  daily_reminder_time: string;
  shopping_window_days: number;
  include_today: boolean;
  include_pantry_items: boolean;
  group_by_category: boolean;
  timezone: string;
  last_sent_at: string | null;
  last_error: string | null;
};

export type TelegramSettingsInput = {
  enabled?: boolean;
  daily_reminder_time?: string;
  shopping_window_days?: number;
  include_today?: boolean;
  include_pantry_items?: boolean;
  group_by_category?: boolean;
  timezone?: string;
};

export type TelegramSendResult = {
  sent: boolean;
  detail: string;
  recipient_count: number;
};

export function fetchTelegramSettings(token: string): Promise<TelegramSettings> {
  return apiRequest<TelegramSettings>("/api/telegram/settings", { token });
}

export function fetchTelegramSubscribers(token: string): Promise<TelegramSubscriber[]> {
  return apiRequest<TelegramSubscriber[]>("/api/telegram/subscribers", { token });
}

export function updateTelegramSettings(
  token: string,
  payload: TelegramSettingsInput,
): Promise<TelegramSettings> {
  return apiRequest<TelegramSettings>("/api/telegram/settings", {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

export function sendTelegramTest(token: string): Promise<TelegramSendResult> {
  return apiRequest<TelegramSendResult>("/api/telegram/test", {
    method: "POST",
    token,
  });
}

export function sendTelegramDailyReminder(token: string): Promise<TelegramSendResult> {
  return apiRequest<TelegramSendResult>("/api/telegram/send-daily-reminder", {
    method: "POST",
    token,
  });
}

export function sendShoppingListTelegram(
  token: string,
  shoppingListId: number,
): Promise<TelegramSendResult> {
  return apiRequest<TelegramSendResult>(`/api/shopping-lists/${shoppingListId}/send-telegram`, {
    method: "POST",
    token,
  });
}
