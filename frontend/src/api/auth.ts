import { apiRequest } from "./client";

export type UserRole = "admin" | "user" | "platform_admin";

export type UserPublic = {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  platform_roles: string[];
  active_household_id: string | null;
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
