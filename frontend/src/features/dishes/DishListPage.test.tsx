import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DishListPage } from "./DishListPage";

const mockFetchDishes = vi.fn();
const mockFetchRecipes = vi.fn();

vi.mock("../../api/catalog", () => ({
  fetchDishes: (...args: unknown[]) => mockFetchDishes(...args),
  fetchRecipes: (...args: unknown[]) => mockFetchRecipes(...args),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    accessToken: "test-token",
    isAdmin: false,
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

const dishes = [
  {
    id: 1,
    public_key: "dish-1",
    name: "Mushroom Risotto",
    description: "Creamy rice",
    default_servings: 4,
    default_prep_time_minutes: null,
    default_cook_time_minutes: null,
    default_difficulty: null,
    course: null,
    status: "active",
    image_url: null,
    suitable_for_lunch: null,
    suitable_for_dinner: null,
    weekday_friendly: null,
    leftovers_possible: null,
    freezer_friendly: null,
    kids_friendly: null,
    thermomix_possible: null,
    active: true,
    notes: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    tag_ids: [],
    computed_traits_json: null,
    seasonality: null,
  },
  {
    id: 2,
    public_key: "dish-2",
    name: "Tomato Pasta",
    description: null,
    default_servings: 2,
    default_prep_time_minutes: null,
    default_cook_time_minutes: null,
    default_difficulty: null,
    course: null,
    status: "active",
    image_url: null,
    suitable_for_lunch: null,
    suitable_for_dinner: null,
    weekday_friendly: null,
    leftovers_possible: null,
    freezer_friendly: null,
    kids_friendly: null,
    thermomix_possible: null,
    active: true,
    notes: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    tag_ids: [],
    computed_traits_json: null,
    seasonality: null,
  },
];

describe("DishListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchDishes.mockResolvedValue(dishes);
    mockFetchRecipes.mockImplementation((_token: string, dishId: number) => {
      if (dishId === 1) {
        return Promise.resolve([{ id: 10, dish_id: 1, variant_name: "Standard", is_main: true }]);
      }
      return Promise.resolve([{ id: 11, dish_id: 2, variant_name: "Quick", is_main: true }]);
    });
  });

  it("filters dishes in real time as the user types", async () => {
    render(
      <MemoryRouter>
        <DishListPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Mushroom Risotto" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tomato Pasta" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search dishes"), { target: { value: "pasta" } });

    expect(screen.queryByRole("heading", { name: "Mushroom Risotto" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tomato Pasta" })).toBeInTheDocument();
  });

  it("matches recipe variant names after recipes load", async () => {
    render(
      <MemoryRouter>
        <DishListPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Mushroom Risotto" })).toBeInTheDocument();
    await waitFor(() => {
      expect(mockFetchRecipes).toHaveBeenCalledTimes(2);
    });

    fireEvent.change(screen.getByLabelText("Search dishes"), { target: { value: "quick" } });

    expect(screen.queryByRole("heading", { name: "Mushroom Risotto" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tomato Pasta" })).toBeInTheDocument();
  });
});
