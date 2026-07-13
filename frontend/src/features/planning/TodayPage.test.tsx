import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TodayPage } from "./TodayPage";

const mockFetchCurrentMealPlan = vi.fn();
const mockFetchDishes = vi.fn();
const mockFetchSchedulerSettings = vi.fn();
const mockFetchMealHistory = vi.fn();
const mockFetchRecipes = vi.fn();

vi.mock("../../api/planning", () => ({
  fetchCurrentMealPlan: (...args: unknown[]) => mockFetchCurrentMealPlan(...args),
  fetchMealPlanByWeek: vi.fn(),
  fetchMealHistory: (...args: unknown[]) => mockFetchMealHistory(...args),
}));

vi.mock("../../api/catalog", () => ({
  fetchDishes: (...args: unknown[]) => mockFetchDishes(...args),
  fetchRecipes: (...args: unknown[]) => mockFetchRecipes(...args),
}));

vi.mock("../../api/scheduler", () => ({
  fetchSchedulerSettings: (...args: unknown[]) => mockFetchSchedulerSettings(...args),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    accessToken: "test-token",
    isAdmin: false,
    user: { id: 1, username: "user", role: "user" },
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

const today = "2026-07-12";

vi.mock("../../lib/datetime", async () => {
  const actual = await vi.importActual<typeof import("../../lib/datetime")>("../../lib/datetime");
  return {
    ...actual,
    todayIsoInTimeZone: () => today,
  };
});

function renderTodayPage() {
  return render(
    <MemoryRouter>
      <TodayPage />
    </MemoryRouter>,
  );
}

describe("TodayPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchDishes.mockResolvedValue([]);
    mockFetchSchedulerSettings.mockResolvedValue({ timezone: "Europe/Paris" });
    mockFetchMealHistory.mockResolvedValue([]);
    mockFetchRecipes.mockResolvedValue([{ id: 99, variant_name: "Standard", is_main: true }]);
  });

  it("shows empty state when nothing is planned for today", async () => {
    mockFetchCurrentMealPlan.mockResolvedValue({
      id: 1,
      week_start_date: "2026-07-06",
      status: "active",
      items: [],
      roulette_undo_available: false,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    renderTodayPage();

    expect(await screen.findByRole("heading", { name: "Today" })).toBeInTheDocument();
    expect(screen.getByText("Nothing planned yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Plan this week" })).toHaveAttribute("href", "/plan");
  });

  it("shows cook and review actions for today's meals", async () => {
    mockFetchCurrentMealPlan.mockResolvedValue({
      id: 1,
      week_start_date: "2026-07-06",
      status: "active",
      items: [
        {
          id: 5,
          meal_plan_id: 1,
          date: today,
          meal_slot: "dinner",
          dish_id: 10,
          recipe_id: 42,
          dish_name: "Tomato Pasta",
          recipe_variant_name: "Standard",
          status: "planned",
          is_locked: false,
          manually_selected: false,
          skip_reason: null,
          skip_comment: null,
          leftover_source_item_id: null,
          selection_reasons_json: null,
          computed_traits_json: null,
          review_saved_at: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
      roulette_undo_available: false,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    renderTodayPage();

    expect(await screen.findByRole("link", { name: "Cook" })).toHaveAttribute("href", "/recipes/42/cook");
    fireEvent.click(screen.getByRole("button", { name: "Review" }));
    expect(screen.getByRole("button", { name: "Ate as planned" })).toBeInTheDocument();
  });
});
