import { apiRequest } from "./client";

export type TelegramSendResult = {
  sent: boolean;
  detail: string;
  recipient_count: number;
};

export function sendShoppingListTelegram(
  token: string,
  shoppingListId: number,
): Promise<TelegramSendResult> {
  return apiRequest<TelegramSendResult>(`/api/shopping-lists/${shoppingListId}/send-telegram`, {
    method: "POST",
    token,
  });
}
