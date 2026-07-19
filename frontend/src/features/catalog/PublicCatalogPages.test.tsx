import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/client";
import { PublicCatalogPage } from "./PublicCatalogPage";
import { PublicRecipeDetailPage } from "./PublicRecipeDetailPage";
import { HouseholdPublicationRequestsPage } from "./HouseholdPublicationRequestsPage";
import {
  PublicCatalogReviewDetailPage,
  PublicCatalogReviewQueuePage,
} from "./PublicCatalogReviewPage";
import { useAuth } from "../auth/AuthContext";
import { resolvePrimaryNav } from "../../app/navigation";
import { AdminRoute } from "../../routes/AdminRoute";

const listPublicRecipes = vi.fn();
const getPublicRecipe = vi.fn();
const adoptPublicRecipe = vi.fn();
const listHouseholdPublicationRequests = vi.fn();
const listPlatformPublicRecipes = vi.fn();
const getPlatformPublicRecipe = vi.fn();
const withdrawPublicationRequest = vi.fn();
const approvePublicRecipe = vi.fn();
const rejectPublicRecipe = vi.fn();
const delistPublicRecipe = vi.fn();

vi.mock("../../api/publicCatalog", () => ({
  listPublicRecipes: (...args: unknown[]) => listPublicRecipes(...args),
  getPublicRecipe: (...args: unknown[]) => getPublicRecipe(...args),
  adoptPublicRecipe: (...args: unknown[]) => adoptPublicRecipe(...args),
  listHouseholdPublicationRequests: (...args: unknown[]) =>
    listHouseholdPublicationRequests(...args),
  listPlatformPublicRecipes: (...args: unknown[]) => listPlatformPublicRecipes(...args),
  getPlatformPublicRecipe: (...args: unknown[]) => getPlatformPublicRecipe(...args),
  withdrawPublicationRequest: (...args: unknown[]) => withdrawPublicationRequest(...args),
  approvePublicRecipe: (...args: unknown[]) => approvePublicRecipe(...args),
  rejectPublicRecipe: (...args: unknown[]) => rejectPublicRecipe(...args),
  delistPublicRecipe: (...args: unknown[]) => delistPublicRecipe(...args),
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
    dish: {
      meal_composition: "main_dish",
      course: "main",
    },
    recipe: {
      recipe_type: "standard",
      servings: 4,
    },
    ingredients: [{ ingredient_display_name: "Pasta", quantity: "200", unit_symbol: "g" }],
    steps: [{ step_number: 1, instruction: "Boil water" }],
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const sampleSide = {
  id: "pub-2",
  status: "public" as const,
  title: "Green Salad",
  description: "Fresh greens",
  current_version: {
    id: "ver-2",
    version_number: 1,
    published_at: "2026-01-01T00:00:00Z",
    superseded_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  snapshot: {
    dish: {
      meal_composition: "simple_dish",
      simple_dish_part: "sidedish",
    },
    recipe: {
      servings: 2,
    },
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const reviewDetailPayload = {
  id: "req-1",
  status: "submitted" as const,
  originating_household_id: "hh-1",
  originating_dish_id: 11,
  originating_recipe_id: 22,
  current_version_id: null,
  submitted_by_user_id: "user-1",
  reviewed_by_user_id: null,
  reviewed_at: null,
  review_note: null,
  title: "Review Detail",
  description: "Outer description",
  latest_version: {
    id: "ver-1",
    version_number: 2,
    published_at: null,
    superseded_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  current_version: null,
  snapshot: {
    dish: {
      name: "Snapshot Pasta",
      description: "Dish description",
      meal_composition: "main_dish",
      simple_dish_part: null,
      course: "main",
      suitable_for_lunch: true,
      suitable_for_dinner: true,
      notes: "Dish notes",
    },
    recipe: {
      variant_name: "Main",
      description: "Recipe description",
      recipe_type: "standard",
      servings: 4,
      prep_time_minutes: 10,
      cook_time_minutes: 20,
      difficulty: "easy",
      source_url: "https://example.com/pasta",
      notes: "Recipe notes",
      is_main: true,
      is_thermomix: false,
    },
    ingredients: [
      {
        ingredient_display_name: "Spaghetti",
        quantity: "400",
        unit_symbol: "g",
        optional: false,
        notes: "Dry",
      },
      {
        ingredient_display_name: "Parmesan",
        quantity: "50",
        unit_symbol: "g",
        optional: true,
      },
    ],
    steps: [
      { step_number: 2, instruction: "Drain pasta" },
      { step_number: 1, instruction: "Boil water", timer_seconds: 60 },
    ],
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

  it("lists public recipes as dish-style cards with snapshot metadata", async () => {
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
    expect(screen.getByRole("heading", { name: "Public Pasta" })).toBeInTheDocument();
    expect(screen.getByText(/Main · Main · Standard/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Public Pasta/i })).toHaveAttribute(
      "href",
      "/catalog/recipes/pub-1",
    );
  });

  it("filters public recipes by title and description text", async () => {
    stubAuth({ accessToken: "token", hasHousehold: true });
    listPublicRecipes.mockResolvedValue([sampleMember, sampleSide]);

    render(
      <MemoryRouter>
        <PublicCatalogPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Public Pasta" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Green Salad" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search public recipes"), {
      target: { value: "greens" },
    });

    expect(screen.queryByRole("heading", { name: "Public Pasta" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Green Salad" })).toBeInTheDocument();
  });

  it("shows Recipe review action on catalog for platform admins", async () => {
    stubAuth({
      accessToken: "token",
      hasHousehold: true,
      isPlatformAdmin: true,
    });
    listPublicRecipes.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <PublicCatalogPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(listPublicRecipes).toHaveBeenCalled();
    });
    expect(screen.getByRole("link", { name: "Recipe review" })).toHaveAttribute(
      "href",
      "/catalog/review",
    );
  });

  it("hides Recipe review action for non-platform household members", async () => {
    stubAuth({
      accessToken: "token",
      hasHousehold: true,
      isPlatformAdmin: false,
      isHouseholdAdmin: false,
    });
    listPublicRecipes.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <PublicCatalogPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(listPublicRecipes).toHaveBeenCalled();
    });
    expect(screen.queryByRole("link", { name: "Recipe review" })).not.toBeInTheDocument();
  });

  it("includes Recipe review in platform primary nav", () => {
    expect(
      resolvePrimaryNav({
        hasHousehold: true,
        isPlatformAdmin: true,
        isHouseholdAdmin: false,
      }).map((item) => item.label),
    ).toContain("Recipe review");
    expect(
      resolvePrimaryNav({
        hasHousehold: true,
        isPlatformAdmin: false,
        isHouseholdAdmin: true,
      }).map((item) => item.label),
    ).not.toContain("Recipe review");
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

  it("withdraws a submitted publication request", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", hasHousehold: true, isHouseholdAdmin: true });
    listHouseholdPublicationRequests
      .mockResolvedValueOnce([
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
      ])
      .mockResolvedValueOnce([
        {
          id: "req-1",
          status: "withdrawn",
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
    withdrawPublicationRequest.mockResolvedValue({
      id: "req-1",
      status: "withdrawn",
      originating_dish_id: 1,
      originating_recipe_id: 2,
      current_version_id: null,
      title: "Pending Pasta",
      description: null,
      review_note: null,
      reviewed_at: null,
      latest_version: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(
      <MemoryRouter>
        <HouseholdPublicationRequestsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Withdraw" })).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Withdraw" }));
    await waitFor(() => {
      expect(withdrawPublicationRequest).toHaveBeenCalledWith("token", "req-1");
    });
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "Withdraw" })).not.toBeInTheDocument();
    });
  });

  it("loads recipe review queue with renamed title", async () => {
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
    expect(screen.getByRole("heading", { name: "Recipe review" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Review Me/i })).toHaveAttribute(
      "href",
      "/catalog/review/req-1",
    );
  });

  it("renders snapshot ingredients and steps on recipe review detail", async () => {
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe.mockResolvedValue(reviewDetailPayload);

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

    expect(screen.getByRole("heading", { name: "Snapshot Pasta" })).toBeInTheDocument();
    expect(screen.getByText("Dish description")).toBeInTheDocument();
    expect(screen.getByText(/400 g Spaghetti/)).toBeInTheDocument();
    expect(screen.getByText(/50 g Parmesan \(optional\)/)).toBeInTheDocument();
    expect(screen.getByText("Boil water")).toBeInTheDocument();
    expect(screen.getByText("Drain pasta")).toBeInTheDocument();
    expect(screen.getByText("https://example.com/pasta")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();

    const technical = screen.getByRole("heading", { name: "Technical metadata" }).closest("section,div");
    expect(technical).toBeTruthy();
    expect(within(technical as HTMLElement).getByText("hh-1")).toBeInTheDocument();
    expect(within(technical as HTMLElement).getByText("11")).toBeInTheDocument();
    expect(within(technical as HTMLElement).getByText("22")).toBeInTheDocument();
  });

  it("approves a submitted request with an optional note", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe
      .mockResolvedValueOnce(reviewDetailPayload)
      .mockResolvedValueOnce({ ...reviewDetailPayload, status: "public" });
    approvePublicRecipe.mockResolvedValue({ ...reviewDetailPayload, status: "public" });

    render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Looks good" } });
    await user.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => {
      expect(approvePublicRecipe).toHaveBeenCalledWith("token", "req-1", "Looks good");
    });
  });

  it("disables Reject and Delist when the review note is empty", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe.mockResolvedValue(reviewDetailPayload);

    const { unmount } = render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Reject" })).toBeDisabled();
    });
    await user.click(screen.getByRole("button", { name: "Reject" }));
    expect(rejectPublicRecipe).not.toHaveBeenCalled();
    unmount();

    getPlatformPublicRecipe.mockResolvedValue({ ...reviewDetailPayload, status: "public" });
    render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delist" })).toBeDisabled();
    });
    await user.click(screen.getByRole("button", { name: "Delist" }));
    expect(delistPublicRecipe).not.toHaveBeenCalled();
  });

  it("rejects a submitted request with a required note", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe
      .mockResolvedValueOnce(reviewDetailPayload)
      .mockResolvedValueOnce({ ...reviewDetailPayload, status: "rejected" });
    rejectPublicRecipe.mockResolvedValue({ ...reviewDetailPayload, status: "rejected" });

    render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Needs work" } });
    await user.click(screen.getByRole("button", { name: "Reject" }));
    await waitFor(() => {
      expect(rejectPublicRecipe).toHaveBeenCalledWith("token", "req-1", "Needs work");
    });
  });

  it("delists a public recipe with a required note", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe
      .mockResolvedValueOnce({ ...reviewDetailPayload, status: "public" })
      .mockResolvedValueOnce({ ...reviewDetailPayload, status: "delisted" });
    delistPublicRecipe.mockResolvedValue({ ...reviewDetailPayload, status: "delisted" });

    render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delist" })).toBeInTheDocument();
    });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Retired" } });
    await user.click(screen.getByRole("button", { name: "Delist" }));
    await waitFor(() => {
      expect(delistPublicRecipe).toHaveBeenCalledWith("token", "req-1", "Retired");
    });
  });

  it("shows review action failures", async () => {
    const user = userEvent.setup();
    stubAuth({ accessToken: "token", isPlatformAdmin: true });
    getPlatformPublicRecipe.mockResolvedValue(reviewDetailPayload);
    approvePublicRecipe.mockRejectedValue(new ApiError("Review note required", 422));

    render(
      <MemoryRouter initialEntries={["/catalog/review/req-1"]}>
        <Routes>
          <Route path="/catalog/review/:publicRecipeId" element={<PublicCatalogReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Approve" }));
    expect(await screen.findByText("Review note required")).toBeInTheDocument();
  });

  it("blocks non-platform users from recipe review via AdminRoute", () => {
    stubAuth({
      user: { id: "2", username: "member" } as ReturnType<typeof useAuth>["user"],
      accessToken: "token",
      isPlatformAdmin: false,
      hasHousehold: true,
    });

    render(
      <MemoryRouter initialEntries={["/catalog/review"]}>
        <Routes>
          <Route element={<AdminRoute />}>
            <Route path="/catalog/review" element={<p>Review queue</p>} />
          </Route>
          <Route path="/today" element={<p>Today</p>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.queryByText("Review queue")).not.toBeInTheDocument();
  });
});
