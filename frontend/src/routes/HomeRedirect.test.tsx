import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { UserPublic } from "../api/auth";
import { useAuth } from "../features/auth/AuthContext";
import { HomeRedirect } from "./HomeRedirect";

vi.mock("../features/auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

type AuthStub = Partial<ReturnType<typeof useAuth>>;

function stubAuth(overrides: AuthStub) {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    accessToken: null,
    loading: false,
    login: vi.fn(),
    loginWithTelegramOtp: vi.fn(),
    refreshUser: vi.fn(),
    logout: vi.fn(),
    isPlatformAdmin: false,
    hasHousehold: false,
    isHouseholdAdmin: false,
    isAdmin: false,
    ...overrides,
  });
}

const householdlessUser: UserPublic = {
  id: "1",
  username: "solo",
  email: "solo@example.com",
  role: "user",
  platform_roles: [],
  active_household_id: null,
  active_household_name: null,
  household_role: null,
  active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderHomeRedirect() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/settings" element={<p>Settings page</p>} />
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("HomeRedirect", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReset();
  });

  it("redirects authenticated householdless non-admin users to /settings", () => {
    stubAuth({
      user: householdlessUser,
      isPlatformAdmin: false,
      hasHousehold: false,
    });
    renderHomeRedirect();
    expect(screen.getByText("Settings page")).toBeInTheDocument();
  });
});
