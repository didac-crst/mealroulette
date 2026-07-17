import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as authApi from "./api/auth";
import { ApiError } from "./api/client";
import { AuthProvider } from "./features/auth/AuthContext";
import * as authStorage from "./features/auth/authStorage";
import { LoginPage } from "./features/auth/LoginPage";

vi.mock("./api/auth", () => ({
  login: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  fetchMe: vi.fn(),
  requestTelegramOtp: vi.fn(),
  verifyTelegramOtp: vi.fn(),
}));

vi.mock("./features/auth/authStorage", () => ({
  loadTokens: vi.fn(() => null),
  saveTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

const meUser = {
  id: "1",
  username: "chef",
  email: "chef@example.com",
  role: "user" as const,
  active_household_id: "00000000-0000-4000-8000-000000000001",
  active_household_name: "Default household",
  household_role: "household_member",
  platform_roles: [] as string[],
  active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const tokens = {
  access_token: "access",
  refresh_token: "refresh",
  token_type: "bearer",
};

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockReset();
    vi.mocked(authApi.fetchMe).mockReset();
    vi.mocked(authApi.requestTelegramOtp).mockReset();
    vi.mocked(authApi.verifyTelegramOtp).mockReset();
    vi.mocked(authStorage.saveTokens).mockReset();
    vi.mocked(authStorage.loadTokens).mockReturnValue(null);
  });

  it("renders the sign-in form", () => {
    renderLogin();

    expect(screen.getByRole("heading", { name: "MealRoulette" })).toBeInTheDocument();
    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(screen.getByText("Plan less. Eat better.")).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "One Time Password" })).toBeInTheDocument();
  });

  it("switches between password and OTP modes", async () => {
    const user = userEvent.setup();
    renderLogin();

    await user.click(screen.getByRole("button", { name: "One Time Password" }));
    expect(screen.getByRole("button", { name: "Send code" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Password" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Password" }));
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("shows notice on OTP request success and locks username", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.requestTelegramOtp).mockResolvedValue({
      detail: "If that account exists and has Telegram linked, a login code was sent.",
    });
    renderLogin();

    await user.click(screen.getByRole("button", { name: "One Time Password" }));
    await user.type(screen.getByLabelText("Username"), "chef");
    await user.click(screen.getByRole("button", { name: "Send code" }));

    expect(await screen.findByText(/login code was sent/i)).toBeInTheDocument();
    expect(authApi.requestTelegramOtp).toHaveBeenCalledWith("chef");
    expect(screen.getByLabelText("Username")).toBeDisabled();
    expect(screen.getByLabelText("Code from Telegram")).toBeInTheDocument();
  });

  it("shows error on OTP request failure", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.requestTelegramOtp).mockRejectedValue(new ApiError("Rate limited", 429));
    renderLogin();

    await user.click(screen.getByRole("button", { name: "One Time Password" }));
    await user.type(screen.getByLabelText("Username"), "chef");
    await user.click(screen.getByRole("button", { name: "Send code" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Rate limited");
    expect(screen.getByLabelText("Username")).not.toBeDisabled();
  });

  it("verifies OTP with locked username and saves tokens after /me", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.requestTelegramOtp).mockResolvedValue({ detail: "Code sent." });
    vi.mocked(authApi.verifyTelegramOtp).mockResolvedValue(tokens);
    vi.mocked(authApi.fetchMe).mockResolvedValue(meUser);
    renderLogin();

    await user.click(screen.getByRole("button", { name: "One Time Password" }));
    await user.type(screen.getByLabelText("Username"), "chef");
    await user.click(screen.getByRole("button", { name: "Send code" }));
    await screen.findByLabelText("Code from Telegram");
    await user.type(screen.getByLabelText("Code from Telegram"), "123456");
    await user.click(screen.getByRole("button", { name: "Sign in with code" }));

    await waitFor(() => {
      expect(authApi.verifyTelegramOtp).toHaveBeenCalledWith("chef", "123456");
      expect(authApi.fetchMe).toHaveBeenCalledWith("access");
      expect(authStorage.saveTokens).toHaveBeenCalledWith({
        accessToken: "access",
        refreshToken: "refresh",
      });
    });
  });

  it("shows error when OTP verify fails", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.requestTelegramOtp).mockResolvedValue({ detail: "Code sent." });
    vi.mocked(authApi.verifyTelegramOtp).mockRejectedValue(new ApiError("Invalid username or code", 401));
    renderLogin();

    await user.click(screen.getByRole("button", { name: "One Time Password" }));
    await user.type(screen.getByLabelText("Username"), "chef");
    await user.click(screen.getByRole("button", { name: "Send code" }));
    await screen.findByLabelText("Code from Telegram");
    await user.type(screen.getByLabelText("Code from Telegram"), "000000");
    await user.click(screen.getByRole("button", { name: "Sign in with code" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid username or code");
    expect(authStorage.saveTokens).not.toHaveBeenCalled();
  });

  it("clears OTP lock when using a different username", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.requestTelegramOtp).mockResolvedValue({ detail: "Code sent." });
    renderLogin();

    await user.click(screen.getByRole("button", { name: "One Time Password" }));
    await user.type(screen.getByLabelText("Username"), "chef");
    await user.click(screen.getByRole("button", { name: "Send code" }));
    await screen.findByRole("button", { name: "Use a different username" });
    await user.click(screen.getByRole("button", { name: "Use a different username" }));

    expect(screen.getByLabelText("Username")).not.toBeDisabled();
    expect(screen.queryByLabelText("Code from Telegram")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send code" })).toBeInTheDocument();
  });
});
