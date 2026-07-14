import { describe, expect, it } from "vitest";

import type { MealPlanItem } from "../../api/planning";
import {
  canExecuteMeal,
  filterReviewItems,
  formatReviewStatus,
  isFutureMealDate,
  isLeftoverSourceCandidate,
  isWithinLeftoverWindow,
  mealSlotSortKey,
  needsReview,
  showReviewExecutionActions,
  showReviewRating,
  showLeftoverSourcePicker,
  showUndoStatus,
  sortMealItems,
  todayIso,
  leftoverSourcesFor,
  selectionReasonsList,
  weekStartForDate,
  canRerollMeal,
  canSwapMeal,
  countNeedsReviewForDate,
  swappableMeals,
  todayMealSlots,
} from "./planFormat";

function item(overrides: Partial<MealPlanItem>): MealPlanItem {
  return {
    id: 1,
    meal_plan_id: 1,
    date: todayIso(),
    meal_slot: "lunch",
    dish_id: null,
    recipe_id: null,
    dish_name: null,
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
    created_at: "",
    updated_at: "",
    ...overrides,
  };
}

describe("planFormat", () => {
  it("treats dates after today as future", () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 2);
    const future = tomorrow.toISOString().slice(0, 10);
    expect(isFutureMealDate(future)).toBe(true);
    expect(isFutureMealDate(todayIso())).toBe(false);
  });

  it("allows execution only for today and past meals", () => {
    expect(canExecuteMeal(item({ date: todayIso() }))).toBe(true);
    expect(canExecuteMeal(item({ date: "2099-01-01" }))).toBe(false);
  });

  it("sorts lunch before dinner on the same day", () => {
    const sorted = sortMealItems([
      item({ id: 2, meal_slot: "dinner" }),
      item({ id: 1, meal_slot: "lunch" }),
    ]);
    expect(sorted.map((entry) => entry.meal_slot)).toEqual(["lunch", "dinner"]);
    expect(mealSlotSortKey("lunch")).toBeLessThan(mealSlotSortKey("dinner"));
  });

  it('shows "Needs review" for past planned meals in review mode', () => {
    expect(formatReviewStatus(item({ status: "planned", date: todayIso() }))).toBe("Needs review");
    expect(formatReviewStatus(item({ status: "planned", date: "2099-01-01" }))).toBe("Planned");
  });

  it("filters needs review to past/today planned meals", () => {
    const items = [
      item({ id: 1, status: "planned", date: todayIso() }),
      item({ id: 2, status: "eaten", date: todayIso(), review_saved_at: "2026-07-03T10:00:00Z" }),
      item({ id: 3, status: "planned", date: "2099-01-01" }),
      item({ id: 4, status: "eaten", date: todayIso(), review_saved_at: null }),
    ];
    expect(filterReviewItems(items, "needs_review").map((entry) => entry.id)).toEqual([1, 4]);
    expect(needsReview(items[0])).toBe(true);
    expect(needsReview(items[1])).toBe(false);
    expect(needsReview(items[3])).toBe(true);
  });

  it("does not need review after ate_leftovers is saved", () => {
    const pending = item({
      status: "ate_leftovers",
      date: todayIso(),
      review_saved_at: null,
    });
    const saved = item({
      status: "ate_leftovers",
      date: todayIso(),
      review_saved_at: "2026-07-03T10:00:00Z",
    });
    expect(needsReview(pending)).toBe(true);
    expect(needsReview(saved)).toBe(false);
  });

  it("shows leftover picker only before leftover review is saved", () => {
    const pending = item({ status: "ate_leftovers", date: todayIso(), review_saved_at: null });
    const saved = item({
      status: "ate_leftovers",
      date: todayIso(),
      review_saved_at: "2026-07-03T10:00:00Z",
    });
    expect(showLeftoverSourcePicker(pending)).toBe(true);
    expect(showLeftoverSourcePicker(saved)).toBe(false);
  });

  it("shows rating only for eaten meals, not leftovers", () => {
    expect(showReviewRating(item({ status: "eaten", date: todayIso() }))).toBe(true);
    expect(showReviewRating(item({ status: "ate_leftovers", date: todayIso() }))).toBe(false);
  });

  it("controls review action visibility by status and date", () => {
    const plannedToday = item({ status: "planned", date: todayIso() });
    const eatenToday = item({ status: "eaten", date: todayIso() });
    const plannedFuture = item({ status: "planned", date: "2099-01-01" });

    expect(showReviewExecutionActions(plannedToday)).toBe(true);
    expect(showReviewExecutionActions(eatenToday)).toBe(false);
    expect(showReviewExecutionActions(plannedFuture)).toBe(false);

    expect(showUndoStatus(eatenToday)).toBe(true);
    expect(showUndoStatus(plannedToday)).toBe(false);
    expect(showUndoStatus(plannedFuture)).toBe(false);
  });

  it("filters leftover sources to eaten meals within 7 days", () => {
    const target = item({ id: 10, date: "2026-07-10" });
    const candidates = [
      item({ id: 1, date: "2026-07-09", status: "eaten", dish_id: 1, dish_name: "Soup" }),
      item({ id: 2, date: "2026-07-02", status: "eaten", dish_id: 2, dish_name: "Old" }),
      item({ id: 3, date: "2026-07-08", status: "ate_leftovers", dish_id: 3, dish_name: "Chain" }),
      item({ id: 4, date: "2026-07-09", status: "skipped", dish_id: 4, dish_name: "Skip" }),
    ];

    expect(isWithinLeftoverWindow("2026-07-03", "2026-07-10")).toBe(true);
    expect(isWithinLeftoverWindow("2026-07-02", "2026-07-10")).toBe(false);
    expect(isLeftoverSourceCandidate(candidates[0], target)).toBe(true);
    expect(isLeftoverSourceCandidate(candidates[1], target)).toBe(false);
    expect(isLeftoverSourceCandidate(candidates[2], target)).toBe(false);
    expect(leftoverSourcesFor(target, candidates).map((entry) => entry.id)).toEqual([1]);
  });

  it("extracts scheduler selection reasons", () => {
    const withReasons = item({
      selection_reasons_json: {
        reasons: ["Helps fish target (1/2 this week)", "Good variety vs neighbouring meals"],
      },
    });
    expect(selectionReasonsList(withReasons)).toEqual([
      "Helps fish target (1/2 this week)",
      "Good variety vs neighbouring meals",
    ]);
    expect(selectionReasonsList(item({ selection_reasons_json: null }))).toEqual([]);
  });

  it("computes Monday week start and reroll eligibility", () => {
    expect(weekStartForDate("2026-07-09")).toBe("2026-07-06");
    expect(canRerollMeal(item({ date: todayIso(), status: "planned", is_locked: false }))).toBe(true);
    expect(canRerollMeal(item({ date: "2020-01-01", status: "planned", is_locked: false }))).toBe(false);
    expect(canRerollMeal(item({ date: todayIso(), status: "planned", is_locked: true }))).toBe(false);
    expect(canSwapMeal(item({ date: todayIso(), status: "planned", is_locked: true }))).toBe(false);
    expect(
      swappableMeals(item({ id: 1, date: todayIso(), status: "planned", is_locked: false }), [
        item({ id: 2, date: todayIso(), status: "planned", is_locked: true }),
        item({ id: 3, date: todayIso(), status: "planned", is_locked: false }),
      ]).map((entry) => entry.id),
    ).toEqual([3]);
  });

  it("builds today lunch and dinner slots", () => {
    const today = todayIso();
    const slots = todayMealSlots(
      [
        item({ id: 1, date: today, meal_slot: "dinner", dish_name: "Pasta" }),
        item({ id: 2, date: "2020-01-01", meal_slot: "lunch" }),
      ],
      today,
    );
    expect(slots.map((slot) => [slot.meal_slot, slot.item?.id ?? null])).toEqual([
      ["lunch", null],
      ["dinner", 1],
    ]);
    expect(countNeedsReviewForDate([item({ date: today, status: "planned" })], today)).toBe(1);
  });
});
