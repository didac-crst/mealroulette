import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RecipeCookingPage } from "./RecipeCookingPage";

const mockFetchRecipe = vi.fn();
const mockFetchDish = vi.fn();
const mockFetchRecipeSteps = vi.fn();
const mockFetchRecipeIngredients = vi.fn();
const mockFetchUnits = vi.fn();
const mockFetchIngredients = vi.fn();

const mockScheduleCookingTimerAlert = vi.fn();
const mockCancelCookingTimerAlert = vi.fn();
const mockCancelCookingTimerAlertForStep = vi.fn();

vi.mock("../../api/cooking", () => ({
  scheduleCookingTimerAlert: (...args: unknown[]) => mockScheduleCookingTimerAlert(...args),
  cancelCookingTimerAlert: (...args: unknown[]) => mockCancelCookingTimerAlert(...args),
  cancelCookingTimerAlertForStep: (...args: unknown[]) => mockCancelCookingTimerAlertForStep(...args),
}));

vi.mock("./cookingTimerAlarm", () => ({
  primeCookingTimerAudio: vi.fn(),
  requestCookingTimerNotificationPermission: vi.fn().mockResolvedValue(undefined),
  startCookingTimerAlarm: vi.fn(() => vi.fn()),
  stopCookingTimerAlarm: vi.fn(),
}));

vi.mock("../../api/catalog", () => ({
  fetchRecipe: (...args: unknown[]) => mockFetchRecipe(...args),
  fetchDish: (...args: unknown[]) => mockFetchDish(...args),
  fetchRecipeSteps: (...args: unknown[]) => mockFetchRecipeSteps(...args),
  fetchRecipeIngredients: (...args: unknown[]) => mockFetchRecipeIngredients(...args),
  fetchUnits: (...args: unknown[]) => mockFetchUnits(...args),
  fetchIngredients: (...args: unknown[]) => mockFetchIngredients(...args),
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

const dish = {
  id: 10,
  public_key: "dish-key",
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
};

const recipe = {
  id: 42,
  dish_id: 10,
  public_key: "dish-key-001",
  sequence_number: 1,
  variant_name: "Standard",
  description: null,
  recipe_type: "standard",
  is_main: true,
  is_thermomix: false,
  thermomix_model: null,
  source_url: null,
  servings: 2,
  prep_time_minutes: 10,
  cook_time_minutes: 20,
  difficulty: "easy",
  computed_traits_json: null,
  notes: null,
};

function renderCookingPage(recipeId = "42") {
  return render(
    <MemoryRouter initialEntries={[`/recipes/${recipeId}/cook`]}>
      <Routes>
        <Route path="/recipes/:recipeId/cook" element={<RecipeCookingPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RecipeCookingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockScheduleCookingTimerAlert.mockResolvedValue({ id: 99, telegram_scheduled: false });
    mockCancelCookingTimerAlert.mockResolvedValue(undefined);
    mockCancelCookingTimerAlertForStep.mockResolvedValue(undefined);
    mockFetchRecipe.mockResolvedValue(recipe);
    mockFetchDish.mockResolvedValue(dish);
    mockFetchRecipeSteps.mockResolvedValue([
      { id: 1, recipe_id: 42, step_number: 1, instruction: "Boil water.", duration_seconds: null, temperature: null, timer_seconds: null, is_thermomix_step: false },
      { id: 2, recipe_id: 42, step_number: 2, instruction: "Cook pasta.", duration_seconds: null, temperature: null, timer_seconds: null, is_thermomix_step: false },
    ]);
    mockFetchRecipeIngredients.mockResolvedValue([
      { id: 1, recipe_id: 42, ingredient_id: 5, quantity: "200", unit_id: 1, optional: false, notes: null },
    ]);
    mockFetchUnits.mockResolvedValue([{ id: 1, name: "Gram", symbol: "g", dimension: "mass" }]);
    mockFetchIngredients.mockResolvedValue([
      {
        id: 5,
        canonical_name: "pasta",
        display_name: "Pasta",
        category: "carbohydrate",
        food_group: "carbohydrate",
        family: null,
        default_unit_id: 1,
        default_dimension: "mass",
        preferred_shopping_unit_id: null,
        aggregation_unit_id: null,
        aggregation_strategy: null,
        pantry_item: false,
        season_start_month: null,
        season_end_month: null,
        notes: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ]);
  });

  it("renders cooking mode for a recipe with steps", async () => {
    renderCookingPage();

    expect(await screen.findByRole("heading", { name: "Standard" })).toBeInTheDocument();
    expect(screen.getByText("Step 1 of 2")).toBeInTheDocument();
    expect(screen.getByText("Boil water.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Exit" })).toHaveAttribute("href", "/dishes/10/recipes/42");
  });

  it("navigates next and previous through steps", async () => {
    renderCookingPage();

    expect(await screen.findByText("Boil water.")).toBeInTheDocument();
    const previous = screen.getByRole("button", { name: "Previous" });
    const next = screen.getByRole("button", { name: "Next" });

    expect(previous).toBeDisabled();
    expect(next).toBeEnabled();

    fireEvent.click(next);
    expect(screen.getByText("Step 2 of 2")).toBeInTheDocument();
    expect(screen.getByText("Cook pasta.")).toBeInTheDocument();
    expect(next).toBeDisabled();
    expect(previous).toBeEnabled();

    fireEvent.click(previous);
    expect(screen.getByText("Step 1 of 2")).toBeInTheDocument();
  });

  it("shows fallback when recipe has no steps", async () => {
    mockFetchRecipeSteps.mockResolvedValue([]);
    renderCookingPage();

    expect(await screen.findByText("No steps")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("shows start timer when step has timer metadata", async () => {
    mockFetchRecipeSteps.mockResolvedValue([
      {
        id: 1,
        recipe_id: 42,
        step_number: 1,
        instruction: "Simmer sauce.",
        duration_seconds: null,
        temperature: null,
        timer_seconds: 300,
        is_thermomix_step: false,
      },
      {
        id: 2,
        recipe_id: 42,
        step_number: 2,
        instruction: "Serve hot.",
        duration_seconds: null,
        temperature: null,
        timer_seconds: null,
        is_thermomix_step: false,
      },
    ]);
    renderCookingPage();

    expect(await screen.findByText("5 min timer")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start timer" })).toBeInTheDocument();
    expect(screen.getByText("5:00")).toBeInTheDocument();
  });

  it("keeps dismissed timer visible when returning to the step from the bar", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      mockFetchRecipeSteps.mockResolvedValue([
        {
          id: 1,
          recipe_id: 42,
          step_number: 1,
          instruction: "Simmer sauce.",
          duration_seconds: null,
          temperature: null,
          timer_seconds: 3,
          is_thermomix_step: false,
        },
        {
          id: 2,
          recipe_id: 42,
          step_number: 2,
          instruction: "Serve hot.",
          duration_seconds: null,
          temperature: null,
          timer_seconds: null,
          is_thermomix_step: false,
        },
      ]);
      renderCookingPage();

      fireEvent.click(await screen.findByRole("button", { name: "Start timer" }));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3500);
      });
      fireEvent.click(screen.getByRole("button", { name: "Next" }));

      expect(await screen.findByText("Ready!")).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
      expect(screen.queryByLabelText("Active cooking timers")).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Previous" }));
      expect(await screen.findByText("0:00")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps dismissed timer at zero with reset only", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      mockFetchRecipeSteps.mockResolvedValue([
        {
          id: 1,
          recipe_id: 42,
          step_number: 1,
          instruction: "Simmer sauce.",
          duration_seconds: null,
          temperature: null,
          timer_seconds: 3,
          is_thermomix_step: false,
        },
      ]);
      renderCookingPage();

      fireEvent.click(await screen.findByRole("button", { name: "Start timer" }));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3500);
      });

      expect(await screen.findByText("Ready!")).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));

      expect(screen.queryByText("Ready!")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Dismiss" })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Start timer" })).not.toBeInTheDocument();
      expect(screen.getByText("0:00")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Reset" }));
      expect(screen.getByRole("button", { name: "Start timer" })).toBeInTheDocument();
      expect(screen.getByText("0:03")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps a started timer visible after moving to the next step", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      mockFetchRecipeSteps.mockResolvedValue([
        {
          id: 1,
          recipe_id: 42,
          step_number: 1,
          instruction: "Simmer sauce.",
          duration_seconds: null,
          temperature: null,
          timer_seconds: 300,
          is_thermomix_step: false,
        },
        {
          id: 2,
          recipe_id: 42,
          step_number: 2,
          instruction: "Serve hot.",
          duration_seconds: null,
          temperature: null,
          timer_seconds: null,
          is_thermomix_step: false,
        },
      ]);
      renderCookingPage();

      fireEvent.click(await screen.findByRole("button", { name: "Start timer" }));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });
      fireEvent.click(screen.getByRole("button", { name: "Next" }));

      expect(screen.getByLabelText("Active cooking timers")).toBeInTheDocument();
      expect(screen.getByText("Running timers")).toBeInTheDocument();
      expect(screen.getByText("Step 1")).toBeInTheDocument();
      expect(screen.getByText("4:58")).toBeInTheDocument();
      expect(screen.getByText("Serve hot.")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });
});
