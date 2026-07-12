import { describe, expect, it } from "vitest";

import { canOpenCookMode, resolveCookRecipeId } from "./todayMeals";
import type { MealPlanItem } from "../../api/planning";

function item(overrides: Partial<MealPlanItem> = {}): MealPlanItem {
  return {
    id: 1,
    meal_plan_id: 1,
    date: "2026-07-12",
    meal_slot: "dinner",
    dish_id: 10,
    recipe_id: null,
    dish_name: "Pasta",
    recipe_variant_name: null,
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
    ...overrides,
  };
}

describe("todayMeals helpers", () => {
  it("prefers assigned recipe id for cook link", () => {
    expect(
      resolveCookRecipeId(item({ recipe_id: 42 }), [{ id: 99, is_main: true } as never]),
    ).toBe(42);
  });

  it("falls back to main recipe then first recipe", () => {
    const recipes = [
      { id: 2, is_main: false },
      { id: 3, is_main: true },
    ] as never[];
    expect(resolveCookRecipeId(item(), recipes)).toBe(3);
    expect(resolveCookRecipeId(item(), [{ id: 2, is_main: false }] as never[])).toBe(2);
  });

  it("blocks cook mode for leftovers meals", () => {
    expect(canOpenCookMode(item({ status: "ate_leftovers" }))).toBe(false);
    expect(canOpenCookMode(item({ dish_id: null }))).toBe(false);
    expect(canOpenCookMode(item())).toBe(true);
  });
});
