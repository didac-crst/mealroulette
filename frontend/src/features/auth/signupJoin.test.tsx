import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as authApi from "../../api/auth";
import * as householdApi from "../../api/household";
import { ApiError } from "../../api/client";
import { AuthProvider } from "./AuthContext";
import { JoinPage } from "./JoinPage";
import { SignupPage } from "./SignupPage";

vi.mock("../../api/auth", () => ({
  login: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  fetchMe: vi.fn(),
  register: vi.fn(),
  registerWithInvitation: vi.fn(),
}));

vi.mock("../../api/household", () => ({
  acceptHouseholdInvitation: vi.fn(),
}));

const tokenResponse = {
  access_token: "access-token",
  refresh_token: "refresh-token",
  token_type: "bearer",
};

describe("signup and join pages", () => {
  beforeEach(() => {
    vi.stubGlobal("location", { assign: vi.fn() });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("registers a new household", async () => {
    vi.mocked(authApi.register).mockResolvedValue(tokenResponse);

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignupPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Household name"), { target: { value: "Casa" } });
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "didac" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "didac@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "supersecret" } });
    fireEvent.click(screen.getByRole("button", { name: "Create household" }));

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith({
        username: "didac",
        email: "didac@example.com",
        password: "supersecret",
        household_name: "Casa",
      });
    });
    expect(window.location.assign).toHaveBeenCalledWith("/today");
  });

  it("rejects whitespace-only household names before calling the API", async () => {
    vi.mocked(authApi.register).mockResolvedValue(tokenResponse);

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignupPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Household name"), { target: { value: "   " } });
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "didac" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "didac@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "supersecret" } });
    fireEvent.click(screen.getByRole("button", { name: "Create household" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Enter a household name.");
    expect(authApi.register).not.toHaveBeenCalled();
    expect(window.location.assign).not.toHaveBeenCalled();
  });

  it("shows API errors during signup without redirecting", async () => {
    vi.mocked(authApi.register).mockRejectedValue(new ApiError("Username already exists", 409));

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignupPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Household name"), { target: { value: "Casa" } });
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "didac" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "didac@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "supersecret" } });
    fireEvent.click(screen.getByRole("button", { name: "Create household" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Username already exists");
    expect(window.location.assign).not.toHaveBeenCalled();
  });

  it("registers a new user from an invitation token", async () => {
    vi.mocked(authApi.registerWithInvitation).mockResolvedValue(tokenResponse);

    render(
      <MemoryRouter initialEntries={["/join?token=invite-token"]}>
        <AuthProvider>
          <JoinPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "guest" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "guest@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "supersecret" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account and join" }));

    await waitFor(() => {
      expect(authApi.registerWithInvitation).toHaveBeenCalledWith({
        token: "invite-token",
        username: "guest",
        email: "guest@example.com",
        password: "supersecret",
      });
    });
    expect(window.location.assign).toHaveBeenCalledWith("/today");
  });

  it("shows an invalid invitation message when the token is missing", () => {
    render(
      <MemoryRouter initialEntries={["/join"]}>
        <AuthProvider>
          <JoinPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Invalid invitation" })).toBeInTheDocument();
    expect(window.location.assign).not.toHaveBeenCalled();
  });

  it("shows API errors when invitation registration fails", async () => {
    vi.mocked(authApi.registerWithInvitation).mockRejectedValue(new ApiError("Invitation already used", 410));

    render(
      <MemoryRouter initialEntries={["/join?token=invite-token"]}>
        <AuthProvider>
          <JoinPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "guest" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "guest@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "supersecret" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account and join" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invitation already used");
    expect(window.location.assign).not.toHaveBeenCalled();
  });

  it("accepts an invitation for an existing signed-in user", async () => {
    vi.mocked(authApi.fetchMe).mockResolvedValue({
      id: "user-1",
      username: "didac",
      email: "didac@example.com",
      role: "user",
      platform_roles: [],
      active_household_id: null,
      active_household_name: null,
      household_role: null,
      active: true,
      created_at: "2026-07-16T00:00:00Z",
      updated_at: "2026-07-16T00:00:00Z",
    });
    vi.mocked(householdApi.acceptHouseholdInvitation).mockResolvedValue();
    window.localStorage.setItem("mealroulette_access_token", "access-token");
    window.localStorage.setItem("mealroulette_refresh_token", "refresh-token");

    render(
      <MemoryRouter initialEntries={["/join?token=invite-token"]}>
        <AuthProvider>
          <JoinPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("button", { name: "Accept invitation" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Accept invitation" }));

    await waitFor(() => {
      expect(householdApi.acceptHouseholdInvitation).toHaveBeenCalledWith("invite-token", "access-token");
    });
    expect(window.location.assign).toHaveBeenCalledWith("/today");
  });

  it("shows API errors when invitation acceptance fails", async () => {
    vi.mocked(authApi.fetchMe).mockResolvedValue({
      id: "user-1",
      username: "didac",
      email: "didac@example.com",
      role: "user",
      platform_roles: [],
      active_household_id: null,
      active_household_name: null,
      household_role: null,
      active: true,
      created_at: "2026-07-16T00:00:00Z",
      updated_at: "2026-07-16T00:00:00Z",
    });
    vi.mocked(householdApi.acceptHouseholdInvitation).mockRejectedValue(
      new ApiError("User already belongs to an active household", 409),
    );
    window.localStorage.setItem("mealroulette_access_token", "access-token");
    window.localStorage.setItem("mealroulette_refresh_token", "refresh-token");

    render(
      <MemoryRouter initialEntries={["/join?token=invite-token"]}>
        <AuthProvider>
          <JoinPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("button", { name: "Accept invitation" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Accept invitation" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("User already belongs to an active household");
    expect(window.location.assign).not.toHaveBeenCalled();
  });
});
