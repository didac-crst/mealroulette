import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { UserPublic } from "../api/auth";
import { useAuth } from "../features/auth/AuthContext";
import { HouseholdMemberRoute } from "./HouseholdMemberRoute";
import { IngredientCatalogRoute } from "./IngredientCatalogRoute";

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

const baseUser: UserPublic = {
  id: "1",
  username: "chef",
  email: "chef@example.com",
  role: "user",
  platform_roles: [],
  active_household_id: "00000000-0000-4000-8000-000000000001",
  active_household_name: "Home",
  household_role: "household_member",
  active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderMemberRoute() {
  return render(
    <MemoryRouter initialEntries={["/today"]}>
      <Routes>
        <Route element={<HouseholdMemberRoute />}>
          <Route path="/today" element={<p>Member outlet</p>} />
        </Route>
        <Route path="/ingredients" element={<p>Ingredients page</p>} />
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderIngredientRoute() {
  return render(
    <MemoryRouter initialEntries={["/ingredients"]}>
      <Routes>
        <Route element={<IngredientCatalogRoute />}>
          <Route path="/ingredients" element={<p>Catalog outlet</p>} />
        </Route>
        <Route path="/today" element={<p>Today page</p>} />
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("HouseholdMemberRoute", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReset();
  });

  it("shows loading state while session resolves", () => {
    stubAuth({ loading: true });
    renderMemberRoute();
    expect(screen.getByText(/Loading session/i)).toBeInTheDocument();
  });

  it("redirects platform admin without household to /ingredients", () => {
    stubAuth({
      user: { ...baseUser, active_household_id: null, active_household_name: null, household_role: null },
      isPlatformAdmin: true,
      hasHousehold: false,
    });
    renderMemberRoute();
    expect(screen.getByText("Ingredients page")).toBeInTheDocument();
  });

  it("redirects non-admin without household to /login", () => {
    stubAuth({
      user: { ...baseUser, active_household_id: null, active_household_name: null, household_role: null },
      isPlatformAdmin: false,
      hasHousehold: false,
    });
    renderMemberRoute();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders outlet when user has a household", () => {
    stubAuth({
      user: baseUser,
      hasHousehold: true,
    });
    renderMemberRoute();
    expect(screen.getByText("Member outlet")).toBeInTheDocument();
  });
});

describe("IngredientCatalogRoute", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReset();
  });

  it("shows loading state while session resolves", () => {
    stubAuth({ loading: true });
    renderIngredientRoute();
    expect(screen.getByText(/Loading session/i)).toBeInTheDocument();
  });

  it("allows platform admin with a household through to outlet", () => {
    stubAuth({
      user: { ...baseUser, role: "platform_admin", platform_roles: ["platform_admin"] },
      isPlatformAdmin: true,
      hasHousehold: true,
    });
    renderIngredientRoute();
    expect(screen.getByText("Catalog outlet")).toBeInTheDocument();
  });

  it("allows platform admin without a household through to outlet", () => {
    stubAuth({
      user: {
        ...baseUser,
        role: "platform_admin",
        platform_roles: ["platform_admin"],
        active_household_id: null,
        active_household_name: null,
        household_role: null,
      },
      isPlatformAdmin: true,
      hasHousehold: false,
    });
    renderIngredientRoute();
    expect(screen.getByText("Catalog outlet")).toBeInTheDocument();
  });

  it("allows household admin through to outlet", () => {
    stubAuth({
      user: { ...baseUser, household_role: "household_admin" },
      isHouseholdAdmin: true,
      hasHousehold: true,
    });
    renderIngredientRoute();
    expect(screen.getByText("Catalog outlet")).toBeInTheDocument();
  });

  it("allows household members through to outlet", () => {
    stubAuth({
      user: baseUser,
      hasHousehold: true,
      isHouseholdAdmin: false,
      isPlatformAdmin: false,
    });
    renderIngredientRoute();
    expect(screen.getByText("Catalog outlet")).toBeInTheDocument();
  });

  it("redirects users without household or platform admin to /login", () => {
    stubAuth({
      user: { ...baseUser, active_household_id: null, active_household_name: null, household_role: null },
      hasHousehold: false,
      isHouseholdAdmin: false,
      isPlatformAdmin: false,
    });
    renderIngredientRoute();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects unauthenticated users to /login", () => {
    stubAuth({ user: null });
    renderIngredientRoute();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });
});
