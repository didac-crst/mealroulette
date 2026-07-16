import { apiRequest } from "./client";

export type HouseholdRole = "household_admin" | "household_member";

export type Household = {
  id: string;
  name: string;
};

export type HouseholdMember = {
  membership_id: string;
  user_id: string;
  username: string;
  email: string;
  role: HouseholdRole;
  joined_at: string;
};

export type HouseholdInvitation = {
  id: string;
  expires_at: string;
  created_at: string;
  accepted_at: string | null;
};

export type HouseholdInvitationCreated = {
  invitation: HouseholdInvitation;
  invite_url: string;
};

export async function fetchHousehold(token: string): Promise<Household> {
  return apiRequest<Household>("/api/household", { token });
}

export async function updateHousehold(token: string, name: string): Promise<Household> {
  return apiRequest<Household>("/api/household", {
    method: "PATCH",
    token,
    body: JSON.stringify({ name }),
  });
}

export async function listHouseholdMembers(token: string): Promise<HouseholdMember[]> {
  return apiRequest<HouseholdMember[]>("/api/household/members", { token });
}

export async function updateMemberRole(
  token: string,
  membershipId: string,
  role: HouseholdRole,
): Promise<HouseholdMember> {
  return apiRequest<HouseholdMember>(`/api/household/members/${membershipId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ role }),
  });
}

export async function removeHouseholdMember(token: string, membershipId: string): Promise<void> {
  await apiRequest<void>(`/api/household/members/${membershipId}`, {
    method: "DELETE",
    token,
  });
}

export async function createHouseholdInvitation(token: string): Promise<HouseholdInvitationCreated> {
  return apiRequest<HouseholdInvitationCreated>("/api/household/invitations", {
    method: "POST",
    token,
  });
}

export async function listHouseholdInvitations(token: string): Promise<HouseholdInvitation[]> {
  return apiRequest<HouseholdInvitation[]>("/api/household/invitations", { token });
}

export async function revokeHouseholdInvitation(token: string, invitationId: string): Promise<void> {
  await apiRequest<void>(`/api/household/invitations/${invitationId}`, {
    method: "DELETE",
    token,
  });
}

export async function acceptHouseholdInvitation(invitationToken: string, accessToken: string): Promise<void> {
  await apiRequest<void>("/api/household/invitations/accept", {
    method: "POST",
    token: accessToken,
    body: JSON.stringify({ token: invitationToken }),
  });
}

export type TelegramLinkToken = {
  token: string;
  expires_at: string;
  deep_link_url: string | null;
};

export type TelegramLinkStatus = {
  linked: boolean;
  username?: string | null;
  display_name?: string | null;
  linked_at?: string | null;
};

export async function createTelegramLinkToken(token: string): Promise<TelegramLinkToken> {
  return apiRequest<TelegramLinkToken>("/api/household/telegram/link-token", {
    method: "POST",
    token,
  });
}

export async function fetchTelegramLink(token: string): Promise<TelegramLinkStatus> {
  return apiRequest<TelegramLinkStatus>("/api/household/telegram/link", { token });
}

export async function unlinkTelegram(token: string): Promise<void> {
  await apiRequest<void>("/api/household/telegram/link", {
    method: "DELETE",
    token,
  });
}

export type NotificationSubscription = {
  notify_daily_reminder: boolean;
  notify_shopping: boolean;
  notify_roulette: boolean;
  daily_reminder_time: string;
  shopping_window_days: number;
  timezone: string;
  last_reminder_sent_at: string | null;
};

export type NotificationSubscriptionInput = Partial<{
  notify_daily_reminder: boolean;
  notify_shopping: boolean;
  notify_roulette: boolean;
  daily_reminder_time: string;
  shopping_window_days: number;
  timezone: string;
}>;

export async function fetchNotificationSubscription(token: string): Promise<NotificationSubscription> {
  return apiRequest<NotificationSubscription>("/api/household/notification-subscription", { token });
}

export async function updateNotificationSubscription(
  token: string,
  payload: NotificationSubscriptionInput,
): Promise<NotificationSubscription> {
  return apiRequest<NotificationSubscription>("/api/household/notification-subscription", {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

export type TelegramSendResult = {
  sent: boolean;
  detail: string;
  recipient_count: number;
};

export async function sendPersonalTelegramTest(token: string): Promise<TelegramSendResult> {
  return apiRequest<TelegramSendResult>("/api/household/telegram/test", {
    method: "POST",
    token,
  });
}

export async function sendPersonalDailyReminder(token: string): Promise<TelegramSendResult> {
  return apiRequest<TelegramSendResult>("/api/household/telegram/send-daily-reminder", {
    method: "POST",
    token,
  });
}
