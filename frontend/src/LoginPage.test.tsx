import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "./features/auth/AuthContext";
import { LoginPage } from "./features/auth/LoginPage";

vi.mock("./api/auth", () => ({
  login: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  fetchMe: vi.fn(),
}));

describe("LoginPage", () => {
  it("renders the sign-in form", () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "MealRoulette" })).toBeInTheDocument();
    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(screen.getByText("Plan less. Eat better.")).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "One Time Password" })).toBeInTheDocument();
    expect(screen.getByText("New here?")).toBeInTheDocument();
  });
});
