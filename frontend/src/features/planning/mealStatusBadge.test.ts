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

  it("marks past planned meals as warning in today mode", () => {
    expect(mealStatusBadgeVariant(item({ status: "planned" }), "today")).toBe("warning");
  });

  it("does not mark future planned meals as warning in review mode", () => {
    expect(mealStatusBadgeVariant(item({ status: "planned", date: "2099-12-31" }), "review")).toBe("default");
  });

  it("marks manually selected planned meals as info in plan mode", () => {
    expect(mealStatusBadgeVariant(item({ manually_selected: true, status: "planned" }), "plan")).toBe("info");
  });

  it("marks locked planned meals as info in plan mode", () => {
    expect(mealStatusBadgeVariant(item({ is_locked: true, status: "planned" }), "plan")).toBe("info");
  });

  it("marks eaten meals as success", () => {
    expect(mealStatusBadgeVariant(item({ status: "eaten" }), "plan")).toBe("success");
  });

  it("marks skipped meals as muted", () => {
    expect(mealStatusBadgeVariant(item({ status: "skipped" }), "plan")).toBe("muted");
  });
});
