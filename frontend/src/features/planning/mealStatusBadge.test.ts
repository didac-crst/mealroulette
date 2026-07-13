import { describe, expect, it } from "vitest";

import type { MealPlanItem } from "../../api/planning";

import { mealStatusBadgeVariant } from "./mealStatusBadge";
import { todayIso } from "./planFormat";

function item(overrides: Partial<MealPlanItem> = {}): MealPlanItem {
  return {
    id: 1,
    meal_plan_id: 1,
    date: todayIso(),
    meal_slot: "dinner",
    dish_id: 1,
    recipe_id: 1,
    dish_name: "Test",
    recipe_variant_name: "Main",
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

describe("mealStatusBadgeVariant", () => {
  it("marks past planned meals as warning in review mode", () => {
    expect(mealStatusBadgeVariant(item({ status: "planned" }), "review")).toBe("warning");
  });

  it("marks eaten meals as success", () => {
    expect(mealStatusBadgeVariant(item({ status: "eaten" }), "plan")).toBe("success");
  });
});
