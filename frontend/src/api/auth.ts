import { apiRequest } from "./client";

export type UserRole = "admin" | "user" | "platform_admin";

export type UserPublic = {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  platform_roles: string[];
  active_household_id: string | null;
  active_household_name: string | null;
  household_role: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export async function login(username: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export async function logout(refreshToken: string): Promise<void> {
  await apiRequest<void>("/api/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export async function fetchMe(token: string): Promise<UserPublic> {
  return apiRequest<UserPublic>("/api/auth/me", { token });
}

export async function changePassword(
  token: string,
  payload: { current_password: string; new_password: string },
): Promise<void> {
  await apiRequest<void>("/api/auth/change-password", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function requestTelegramOtp(username: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>("/api/auth/telegram-otp/request", {
    method: "POST",
    body: JSON.stringify({ username }),
  });
}

export async function verifyTelegramOtp(username: string, code: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/auth/telegram-otp/verify", {
    method: "POST",
    body: JSON.stringify({ username, code }),
  });
}

export async function register(payload: {
  username: string;
  email: string;
  password: string;
  household_name: string;
}): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function registerWithInvitation(payload: {
  token: string;
  username: string;
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/auth/register-with-invitation", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
