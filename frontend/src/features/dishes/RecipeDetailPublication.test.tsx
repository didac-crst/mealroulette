import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RecipeDetailPage } from "./RecipeDetailPage";
import { useAuth } from "../auth/AuthContext";

vi.mock("../../api/catalog", () => ({
  fetchDish: vi.fn().mockResolvedValue({
    id: 1,
    public_key: "dish-key",
    name: "Pasta",
    description: null,
    default_servings: 2,
    course: null,
    meal_composition: "main_dish",
    simple_dish_part: null,
    status: "active",
    tag_ids: [],
  }),
  fetchTags: vi.fn().mockResolvedValue([]),
  fetchRecipe: vi.fn().mockResolvedValue({
    id: 2,
    dish_id: 1,
    public_key: "recipe-key",
    sequence_number: 1,
    variant_name: "Main",
    description: null,
    recipe_type: "standard",
    is_main: true,
    is_thermomix: false,
    thermomix_model: null,
    source_url: null,
    servings: 2,
    prep_time_minutes: null,
    cook_time_minutes: null,
    difficulty: null,
    computed_traits_json: null,
    notes: null,
  }),
  fetchRecipeSteps: vi.fn().mockResolvedValue([]),
  fetchRecipeIngredients: vi.fn().mockResolvedValue([]),
  fetchUnits: vi.fn().mockResolvedValue([]),
  fetchIngredients: vi.fn().mockResolvedValue([]),
}));

vi.mock("../../api/publicCatalog", () => ({
  submitPublishRequest: vi.fn(),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("./RecipeCompositionChart", () => ({
  RecipeCompositionChart: () => null,
}));

vi.mock("./CookingIngredientList", () => ({
  CookingIngredientList: () => null,
}));

vi.mock("./DishClassificationSummary", () => ({
  DishInheritedContext: () => null,
}));

type AuthStub = Partial<ReturnType<typeof useAuth>>;

function stubAuth(overrides: AuthStub) {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    accessToken: "token",
    loading: false,
    login: vi.fn(),
    loginWithTelegramOtp: vi.fn(),
    refreshUser: vi.fn(),
    logout: vi.fn(),
    isPlatformAdmin: false,
    hasHousehold: true,
    isHouseholdAdmin: false,
    isAdmin: false,
    ...overrides,
  });
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/dishes/1/recipes/2"]}>
      <Routes>
        <Route path="/dishes/:dishId/recipes/:recipeId" element={<RecipeDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RecipeDetailPage publication action", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Request publication only for household admins", async () => {
    stubAuth({ isHouseholdAdmin: false });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Main" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Request publication" })).not.toBeInTheDocument();
  });

  it("shows Request publication for household admins", async () => {
    stubAuth({ isHouseholdAdmin: true });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Request publication" })).toBeInTheDocument();
    });
  });
});
