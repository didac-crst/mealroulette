import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminSettingsPage } from "./AdminSettingsPage";

const useAuthMock = vi.fn();

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("./HouseholdClock", () => ({
  HouseholdClock: () => <p>Household clock</p>,
}));

function renderSettings() {
  return render(
    <MemoryRouter initialEntries={["/settings"]}>
      <Routes>
        <Route path="/settings" element={<AdminSettingsPage />} />
        <Route path="/today" element={<p>Today redirected</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AdminSettingsPage access boundary", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it("redirects unauthenticated users away from settings", async () => {
    useAuthMock.mockReturnValue({
      user: null,
      isPlatformAdmin: false,
      isHouseholdAdmin: false,
      loading: false,
    });

    renderSettings();

    expect(await screen.findByText("Today redirected")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Settings" })).not.toBeInTheDocument();
  });

  it("shows personal settings for ordinary authenticated members", () => {
    useAuthMock.mockReturnValue({
      user: { id: "u1", username: "member" },
      isPlatformAdmin: false,
      isHouseholdAdmin: false,
      loading: false,
    });

    renderSettings();

    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Personal" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Telegram/i })).toHaveAttribute("href", "/settings/telegram");
    expect(screen.queryByRole("heading", { name: "Household" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Meal planning" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Integrations" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Catalog" })).not.toBeInTheDocument();
  });

  it("shows household and planning tiles for household admins", () => {
    useAuthMock.mockReturnValue({
      user: { id: "u1", username: "hadmin" },
      isPlatformAdmin: false,
      isHouseholdAdmin: true,
      loading: false,
    });

    renderSettings();

    expect(screen.getByRole("heading", { name: "Personal" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Household" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Meal planning" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Household Telegram/i })).toHaveAttribute(
      "href",
      "/settings/telegram/household",
    );
    expect(screen.queryByRole("heading", { name: "Integrations" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Catalog" })).not.toBeInTheDocument();
  });

  it("shows integrations and catalog for platform admins", () => {
    useAuthMock.mockReturnValue({
      user: { id: "u1", username: "padmin" },
      isPlatformAdmin: true,
      isHouseholdAdmin: false,
      loading: false,
    });

    renderSettings();

    expect(screen.getByRole("heading", { name: "Personal" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Catalog" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Household" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Meal planning" })).not.toBeInTheDocument();
  });

  it("shows all role-gated groups for dual-role admins", () => {
    useAuthMock.mockReturnValue({
      user: { id: "u1", username: "dual" },
      isPlatformAdmin: true,
      isHouseholdAdmin: true,
      loading: false,
    });

    renderSettings();

    expect(screen.getByText(/Household and platform admin/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Personal" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Household" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Meal planning" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Catalog" })).toBeInTheDocument();
  });

  it("redirects after auth loading resolves to unauthenticated", async () => {
    useAuthMock.mockReturnValue({
      user: null,
      isPlatformAdmin: false,
      isHouseholdAdmin: false,
      loading: true,
    });

    const view = renderSettings();

    expect(screen.getByText(/Loading settings/i)).toBeInTheDocument();
    expect(screen.queryByText("Today redirected")).not.toBeInTheDocument();

    useAuthMock.mockReturnValue({
      user: null,
      isPlatformAdmin: false,
      isHouseholdAdmin: false,
      loading: false,
    });
    view.rerender(
      <MemoryRouter initialEntries={["/settings"]}>
        <Routes>
          <Route path="/settings" element={<AdminSettingsPage />} />
          <Route path="/today" element={<p>Today redirected</p>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Today redirected")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(/Loading settings/i)).not.toBeInTheDocument();
    });
  });
});
