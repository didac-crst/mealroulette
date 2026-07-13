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
  }),
}));

vi.mock("../features/auth/authStorage", () => ({
  loadTokens: vi.fn(() => null),
  saveTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

function renderShell(initialPath = "/today") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/today" element={<p>Today content</p>} />
            <Route path="/settings" element={<p>Settings content</p>} />
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
});
