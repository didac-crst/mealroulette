import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminRoute } from "./AdminRoute";
import { useAuth } from "../features/auth/AuthContext";

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

function renderReviewGate() {
  return render(
    <MemoryRouter initialEntries={["/catalog/review"]}>
      <Routes>
        <Route element={<AdminRoute />}>
          <Route path="/catalog/review" element={<p>Review queue</p>} />
        </Route>
        <Route path="/today" element={<p>Today</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AdminRoute catalog review gate", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReset();
  });

  it("allows platform admins into /catalog/review", () => {
    stubAuth({
      user: { id: "1", username: "admin" } as ReturnType<typeof useAuth>["user"],
      isPlatformAdmin: true,
    });
    renderReviewGate();
    expect(screen.getByText("Review queue")).toBeInTheDocument();
  });

  it("redirects non-platform users away from /catalog/review", () => {
    stubAuth({
      user: { id: "2", username: "member" } as ReturnType<typeof useAuth>["user"],
      isPlatformAdmin: false,
      hasHousehold: true,
    });
    renderReviewGate();
    expect(screen.getByText("Today")).toBeInTheDocument();
  });
});
