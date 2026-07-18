import { render, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { IngredientListPage } from "./IngredientListPage";
import { useAuth } from "../auth/AuthContext";

const fetchIngredients = vi.fn();
const fetchUnits = vi.fn();

vi.mock("../../api/catalog", () => ({
  fetchIngredients: (...args: unknown[]) => fetchIngredients(...args),
  fetchUnits: (...args: unknown[]) => fetchUnits(...args),
}));

vi.mock("../auth/AuthContext", () => ({
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

function renderPage() {
  return render(
    <MemoryRouter>
      <IngredientListPage />
    </MemoryRouter>,
  );
}

function headerActions() {
  return within(document.querySelector(".page-header-actions") as HTMLElement);
}

describe("IngredientListPage action visibility", () => {
  beforeEach(() => {
    fetchIngredients.mockReset();
    fetchUnits.mockReset();
    fetchIngredients.mockResolvedValue([]);
    fetchUnits.mockResolvedValue([]);
  });

  it("shows Ingredient proposals for household members and hides admin actions", async () => {
    stubAuth({
      accessToken: "token",
      hasHousehold: true,
      isHouseholdAdmin: false,
      isPlatformAdmin: false,
    });

    renderPage();

    await waitFor(() => {
      expect(fetchIngredients).toHaveBeenCalledWith("token", undefined);
    });

    expect(headerActions().getByRole("link", { name: "Ingredient proposals" })).toBeInTheDocument();
    expect(headerActions().queryByRole("link", { name: "Taxonomy" })).not.toBeInTheDocument();
    expect(headerActions().queryByRole("link", { name: "Proposal review" })).not.toBeInTheDocument();
    expect(headerActions().queryByRole("link", { name: "Add ingredient" })).not.toBeInTheDocument();
  });

  it("shows Ingredient proposals and Taxonomy for household admins", async () => {
    stubAuth({
      accessToken: "token",
      hasHousehold: true,
      isHouseholdAdmin: true,
      isPlatformAdmin: false,
    });

    renderPage();

    await waitFor(() => {
      expect(fetchIngredients).toHaveBeenCalled();
    });

    expect(headerActions().getByRole("link", { name: "Ingredient proposals" })).toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Taxonomy" })).toBeInTheDocument();
    expect(headerActions().queryByRole("link", { name: "Proposal review" })).not.toBeInTheDocument();
    expect(headerActions().queryByRole("link", { name: "Add ingredient" })).not.toBeInTheDocument();
  });

  it("shows all actions for platform admins with a household", async () => {
    stubAuth({
      accessToken: "token",
      hasHousehold: true,
      isHouseholdAdmin: false,
      isPlatformAdmin: true,
    });

    renderPage();

    await waitFor(() => {
      expect(fetchIngredients).toHaveBeenCalled();
    });

    expect(headerActions().getByRole("link", { name: "Ingredient proposals" })).toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Taxonomy" })).toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Proposal review" })).toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Add ingredient" })).toBeInTheDocument();
  });

  it("shows platform admin actions without Ingredient proposals when no household", async () => {
    stubAuth({
      accessToken: "token",
      hasHousehold: false,
      isHouseholdAdmin: false,
      isPlatformAdmin: true,
    });

    renderPage();

    await waitFor(() => {
      expect(fetchIngredients).toHaveBeenCalled();
    });

    expect(headerActions().queryByRole("link", { name: "Ingredient proposals" })).not.toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Taxonomy" })).toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Proposal review" })).toBeInTheDocument();
    expect(headerActions().getByRole("link", { name: "Add ingredient" })).toBeInTheDocument();
  });
});
