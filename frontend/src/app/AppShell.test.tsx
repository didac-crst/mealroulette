import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthContext";
import { AppShell } from "./AppShell";

vi.mock("../api/auth", () => ({
  login: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  fetchMe: vi.fn().mockResolvedValue({
    id: 1,
    username: "chef",
    email: "chef@example.com",
    role: "user",
    active_household_id: "00000000-0000-4000-8000-000000000001",
    active_household_name: "Default household",
    household_role: "household_member",
    platform_roles: [],
  }),
}));

vi.mock("../features/auth/authStorage", () => ({
  loadTokens: vi.fn(() => ({
    accessToken: "test-access-token",
    refreshToken: "test-refresh-token",
  })),
  saveTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

vi.mock("../features/planning/useReviewAttentionCount", () => ({
  useReviewAttentionCount: vi.fn(() => false),
}));

function renderShell(initialPath = "/today") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/today" element={<p>Today content</p>} />
            <Route path="/settings" element={<p>Settings content</p>} />
            <Route path="/recipes/:id/cook" element={<p>Cooking content</p>} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("AppShell", () => {
  it("renders mobile bottom navigation with Shopping label", async () => {
    renderShell();

    expect(await screen.findByText("Today content")).toBeInTheDocument();
    const mobileNav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(mobileNav).toHaveTextContent("Shopping");
    expect(mobileNav).not.toHaveTextContent("List");
  });

  it("exposes desktop sidebar navigation landmark", async () => {
    renderShell();

    expect(await screen.findByText("Today content")).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Application navigation" })).toBeInTheDocument();
  });

  it("provides skip link and main content landmark", async () => {
    renderShell();

    expect(await screen.findByText("Today content")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute("href", "#main-content");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
  });

  it("hides shell navigation in cooking mode", async () => {
    renderShell("/recipes/1/cook");

    expect(await screen.findByText("Cooking content")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Skip to main content" })).not.toBeInTheDocument();
    expect(screen.queryByRole("complementary", { name: "Application navigation" })).not.toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Primary navigation" })).not.toBeInTheDocument();
  });

  it("does not show Ingredients for household members", async () => {
    renderShell();

    expect(await screen.findByText("Today content")).toBeInTheDocument();
    const sidebar = screen.getByRole("complementary", { name: "Application navigation" });
    expect(sidebar).toHaveTextContent("Dishes");
    expect(sidebar).not.toHaveTextContent("Ingredients");
  });
});
