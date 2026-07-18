import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PublicCatalogPage } from "./PublicCatalogPage";
import { PublicRecipeDetailPage } from "./PublicRecipeDetailPage";
import { HouseholdPublicationRequestsPage } from "./HouseholdPublicationRequestsPage";
import {
  PublicCatalogReviewDetailPage,
  PublicCatalogReviewQueuePage,
} from "./PublicCatalogReviewPage";
import { useAuth } from "../auth/AuthContext";

const listPublicRecipes = vi.fn();
const getPublicRecipe = vi.fn();
const adoptPublicRecipe = vi.fn();
const listHouseholdPublicationRequests = vi.fn();
const listPlatformPublicRecipes = vi.fn();
const getPlatformPublicRecipe = vi.fn();

vi.mock("../../api/publicCatalog", () => ({
  listPublicRecipes: (...args: unknown[]) => listPublicRecipes(...args),
  getPublicRecipe: (...args: unknown[]) => getPublicRecipe(...args),
  adoptPublicRecipe: (...args: unknown[]) => adoptPublicRecipe(...args),
  listHouseholdPublicationRequests: (...args: unknown[]) =>
    listHouseholdPublicationRequests(...args),
  listPlatformPublicRecipes: (...args: unknown[]) => listPlatformPublicRecipes(...args),
  getPlatformPublicRecipe: (...args: unknown[]) => getPlatformPublicRecipe(...args),
  withdrawPublicationRequest: vi.fn(),
  approvePublicRecipe: vi.fn(),
  rejectPublicRecipe: vi.fn(),
  delistPublicRecipe: vi.fn(),
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

const sampleMember = {
  id: "pub-1",
  status: "public" as const,
  title: "Public Pasta",
  description: "A shared pasta",
  current_version: {
    id: "ver-1",
    version_number: 1,
    published_at: "2026-01-01T00:00:00Z",
    superseded_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  snapshot: {
    ingredients: [{ ingredient_display_name: "Pasta", quantity: "200", unit_symbol: "g" }],
    steps: [{ step_number: 1, instruction: "Boil water" }],
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("public catalog frontend smoke", () => {
  beforeEach(() => {
    listPublicRecipes.mockReset();
    getPublicRecipe.mockReset();
    adoptPublicRecipe.mockReset();
    listHouseholdPublicationRequests.mockReset();
    listPlatformPublicRecipes.mockReset();
    getPlatformPublicRecipe.mockReset();
  });

  it("lists public recipes and links to detail", async () => {
    stubAuth({ accessToken: "token", hasHousehold: true });
    listPublicRecipes.mockResolvedValue([sampleMember]);

    render(
      <MemoryRouter>
        <PublicCatalogPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(listPublicRecipes).toHaveBeenCalledWith("token");
    });
    expect(screen.getByRole("link", { name: /Public Pasta/i })).toHaveAttribute(
      "href",
      "/catalog/recipes/pub-1",
    );
  });

  it("adopts from public recipe detail", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", hasHousehold: true });
    getPublicRecipe.mockResolvedValue(sampleMember);
    adoptPublicRecipe.mockResolvedValue({
      dish_id: 10,
      recipe_id: 20,
      dish_public_key: "dish-key",
      recipe_public_key: "recipe-key",
      derived_from_public_recipe_id: "pub-1",
      derived_from_public_version_id: "ver-1",
    });

    render(
      <MemoryRouter initialEntries={["/catalog/recipes/pub-1"]}>
        <Routes>
          <Route path="/catalog/recipes/:publicRecipeId" element={<PublicRecipeDetailPage />} />
          <Route path="/dishes/:dishId/recipes/:recipeId" element={<p>Adopted</p>} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(getPublicRecipe).toHaveBeenCalledWith("token", "pub-1");
    });
    await user.click(screen.getByRole("button", { name: /Adopt into household/i }));
    await waitFor(() => {
      expect(adoptPublicRecipe).toHaveBeenCalledWith("token", "pub-1");
    });
    expect(await screen.findByText("Adopted")).toBeInTheDocument();
  });

  it("loads household publication requests for household admins", async () => {
    stubAuth({ accessToken: "token", hasHousehold: true, isHouseholdAdmin: true });
    listHouseholdPublicationRequests.mockResolvedValue([
      {
        id: "req-1",
        status: "submitted",
        originating_dish_id: 1,
        originating_recipe_id: 2,
        current_version_id: null,
        title: "Pending Pasta",
        description: null,
        review_note: null,
        reviewed_at: null,
        latest_version: {
          id: "ver-1",
          version_number: 1,
          published_at: null,
          superseded_at: null,
          created_at: "2026-01-01T00:00:00Z",
        },
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ]);

    render(
      <MemoryRouter>
        <HouseholdPublicationRequestsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(listHouseholdPublicationRequests).toHaveBeenCalledWith("token");
    });
    expect(screen.getByText("Pending Pasta")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Withdraw" })).toBeInTheDocument();
  });

  it("loads platform review queue", async () => {
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    listPlatformPublicRecipes.mockResolvedValue([
      {
        id: "req-1",
        status: "submitted",
        originating_household_id: "hh-1",
        originating_dish_id: 1,
        originating_recipe_id: 2,
        current_version_id: null,
        submitted_by_user_id: "user-1",
        reviewed_by_user_id: null,
        reviewed_at: null,
        review_note: null,
        title: "Review Me",
        description: null,
        latest_version: null,
        current_version: null,
        snapshot: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ]);

    render(
      <MemoryRouter>
        <PublicCatalogReviewQueuePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(listPlatformPublicRecipes).toHaveBeenCalledWith("token", "submitted");
    });
    expect(screen.getByRole("link", { name: /Review Me/i })).toHaveAttribute(
      "href",
      "/catalog/review/req-1",
    );
  });

  it("loads platform review detail actions for submitted items", async () => {
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe.mockResolvedValue({
      id: "req-1",
      status: "submitted",
      originating_household_id: "hh-1",
      originating_dish_id: 1,
      originating_recipe_id: 2,
      current_version_id: null,
      submitted_by_user_id: "user-1",
      reviewed_by_user_id: null,
      reviewed_at: null,
      review_note: null,
      title: "Review Detail",
      description: "Notes",
      latest_version: {
        id: "ver-1",
        version_number: 1,
        published_at: null,
        superseded_at: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      current_version: null,
      snapshot: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(getPlatformPublicRecipe).toHaveBeenCalledWith("token", "req-1");
    });
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
  });
});
