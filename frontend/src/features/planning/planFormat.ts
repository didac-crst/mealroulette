import type { MealPlanItem, MealPlanItemStatus, MealSlot } from "../../api/planning";
import { isoDateFromLocalDate } from "../../lib/datetime";

const DAY_FORMAT = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "short", day: "numeric" });

const SLOT_ORDER: Record<MealSlot, number> = { lunch: 0, dinner: 1 };

export function formatNeedsReviewCount(count: number): string {
  if (count === 1) {
    return "1 meal needs review";
  }
  return `${count} meals need review`;
}

export function formatPlanDate(isoDate: string): string {
  return DAY_FORMAT.format(new Date(`${isoDate}T12:00:00`));
}

export function formatSlotLabel(slot: MealSlot): string {
  return slot === "lunch" ? "Lunch" : "Dinner";
}

export function formatStatus(status: MealPlanItemStatus): string {
  switch (status) {
    case "planned":
      return "Planned";
    case "eaten":
      return "Ate as planned";
    case "skipped":
      return "Skipped";
    case "ate_leftovers":
      return "Ate leftovers";
    default:
      return status;
  }
}

export function statusClassName(status: MealPlanItemStatus): string {
  return `meal-status meal-status-${status}`;
}

export function todayIso(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function addDays(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T12:00:00`);
  date.setDate(date.getDate() + days);
  return isoDateFromLocalDate(date);
}

export function addWeeks(weekStart: string, weeks: number): string {
  return addDays(weekStart, weeks * 7);
}

export function isFutureMealDate(isoDate: string): boolean {
  return isoDate > todayIso();
}

export function canExecuteMeal(item: MealPlanItem): boolean {
  return !isFutureMealDate(item.date);
}

export function mealSlotSortKey(slot: MealSlot): number {
  return SLOT_ORDER[slot];
}

export function sortMealItems(items: MealPlanItem[]): MealPlanItem[] {
  return [...items].sort(
    (a, b) => a.date.localeCompare(b.date) || mealSlotSortKey(a.meal_slot) - mealSlotSortKey(b.meal_slot),
  );
}

export function groupItemsByDate(items: MealPlanItem[]): Map<string, MealPlanItem[]> {
  const grouped = new Map<string, MealPlanItem[]>();
  for (const item of sortMealItems(items)) {
    const dayItems = grouped.get(item.date) ?? [];
    dayItems.push(item);
    grouped.set(item.date, dayItems);
  }
  return grouped;
}

export function weekDates(weekStart: string): string[] {
  return Array.from({ length: 7 }, (_, index) => addDays(weekStart, index));
}

const EATEN_STATUSES: MealPlanItemStatus[] = ["eaten", "ate_leftovers"];

export function isEatenStatus(status: MealPlanItemStatus): boolean {
  return EATEN_STATUSES.includes(status);
}

export function todayAndTomorrowItems(items: MealPlanItem[]): MealPlanItem[] {
  const today = todayIso();
  const tomorrow = addDays(today, 1);
  return sortMealItems(items.filter((item) => item.date === today || item.date === tomorrow));
}

export function itemsForDate(items: MealPlanItem[], isoDate: string): MealPlanItem[] {
  return sortMealItems(items.filter((item) => item.date === isoDate));
}

export type TodayMealSlot = {
  meal_slot: MealSlot;
  item: MealPlanItem | null;
};

export function todayMealSlots(items: MealPlanItem[], isoDate: string): TodayMealSlot[] {
  const dayItems = items.filter((item) => item.date === isoDate);
  return (["lunch", "dinner"] as const).map((meal_slot) => ({
    meal_slot,
    item: dayItems.find((item) => item.meal_slot === meal_slot) ?? null,
  }));
}

export function countNeedsReviewForDate(items: MealPlanItem[], isoDate: string): number {
  return itemsForDate(items, isoDate).filter(needsReview).length;
}

export type ReviewFilter = "needs_review" | "all";

export function isExecutionComplete(status: MealPlanItemStatus): boolean {
  return status !== "planned";
}

export function formatReviewStatus(item: MealPlanItem): string {
  if (item.status === "planned" && !isFutureMealDate(item.date)) {
    return "Needs review";
  }
  if (item.status === "planned" && isFutureMealDate(item.date)) {
    return item.is_locked ? "Planned · locked" : "Planned";
  }
  return formatStatus(item.status);
}

export function reviewStatusClassName(item: MealPlanItem): string {
  if (item.status === "planned" && !isFutureMealDate(item.date)) {
    return "meal-status meal-status-not-reviewed";
  }
  return statusClassName(item.status);
}

export function needsReview(item: MealPlanItem): boolean {
  if (!canExecuteMeal(item)) {
    return false;
  }
  if (item.status === "planned") {
    return true;
  }
  return isExecutionComplete(item.status) && item.review_saved_at == null;
}

export function filterReviewItems(items: MealPlanItem[], filter: ReviewFilter): MealPlanItem[] {
  if (filter === "all") {
    return sortMealItems(items);
  }
  return sortMealItems(items.filter(needsReview));
}

export function showPlanModeActions(): boolean {
  return true;
}

export function showReviewExecutionActions(item: MealPlanItem): boolean {
  return canExecuteMeal(item) && item.status === "planned";
}

export function showUndoStatus(item: MealPlanItem): boolean {
  return canExecuteMeal(item) && isExecutionComplete(item.status);
}

export function isReviewedQuiet(item: MealPlanItem): boolean {
  return isExecutionComplete(item.status);
}

export function showReviewRating(item: MealPlanItem): boolean {
  return canExecuteMeal(item) && item.status === "eaten";
}

export function showSkipSummary(item: MealPlanItem): boolean {
  return item.status === "skipped" && canExecuteMeal(item) && item.review_saved_at != null;
}

export function showLeftoverSource(item: MealPlanItem): boolean {
  return item.status === "ate_leftovers";
}

// Keep in sync with backend planning_rules.LEFTOVER_SOURCE_WINDOW_DAYS.
export const LEFTOVER_SOURCE_WINDOW_DAYS = 7;

const SHORT_DAY_FORMAT = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  month: "short",
  day: "numeric",
});

export function formatShortPlanDate(isoDate: string): string {
  return SHORT_DAY_FORMAT.format(new Date(`${isoDate}T12:00:00`));
}

export function formatLeftoverSourceOption(item: MealPlanItem): string {
  const dateLabel = SHORT_DAY_FORMAT.format(new Date(`${item.date}T12:00:00`));
  return `${dateLabel} · ${formatSlotLabel(item.meal_slot)} — ${item.dish_name ?? "Unknown"}`;
}

export function isWithinLeftoverWindow(sourceDate: string, itemDate: string): boolean {
  const earliest = addDays(itemDate, -LEFTOVER_SOURCE_WINDOW_DAYS);
  return sourceDate >= earliest && sourceDate <= itemDate;
}

export function isLeftoverSourceCandidate(candidate: MealPlanItem, item: MealPlanItem): boolean {
  if (candidate.id === item.id) {
    return false;
  }
  if (candidate.status !== "eaten") {
    return false;
  }
  if (!candidate.dish_id || !candidate.dish_name) {
    return false;
  }
  return isWithinLeftoverWindow(candidate.date, item.date);
}

export function showLeftoverSourcePicker(item: MealPlanItem): boolean {
  return item.status === "ate_leftovers" && canExecuteMeal(item) && item.review_saved_at == null;
}

export function showLeftoverSourceSummary(item: MealPlanItem): boolean {
  return item.status === "ate_leftovers" && canExecuteMeal(item) && item.review_saved_at != null;
}

export function leftoverSourceLabel(item: MealPlanItem, planItems: MealPlanItem[]): string | null {
  if (!item.leftover_source_item_id) {
    return null;
  }
  const source = planItems.find((candidate) => candidate.id === item.leftover_source_item_id);
  if (!source) {
    return null;
  }
  return formatLeftoverSourceOption(source);
}

export function leftoverSourcesFor(item: MealPlanItem, planItems: MealPlanItem[]): MealPlanItem[] {
  return sortMealItems(planItems.filter((candidate) => isLeftoverSourceCandidate(candidate, item)));
}

export function weekStartForDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const weekday = date.getUTCDay();
  const mondayOffset = (weekday + 6) % 7;
  date.setUTCDate(date.getUTCDate() - mondayOffset);
  return date.toISOString().slice(0, 10);
}

export function selectionReasonsList(item: MealPlanItem): string[] {
  const payload = item.selection_reasons_json;
  if (!payload || typeof payload !== "object") {
    return [];
  }
  const reasons = (payload as { reasons?: unknown }).reasons;
  if (!Array.isArray(reasons)) {
    return [];
  }
  return reasons.filter((reason): reason is string => typeof reason === "string");
}

export function canRerollMeal(item: MealPlanItem): boolean {
  return item.status === "planned" && !item.is_locked && item.date >= todayIso();
}

export function canSwapMeal(item: MealPlanItem): boolean {
  return item.status === "planned" && !item.is_locked && item.date >= todayIso();
}

export function swappableMeals(item: MealPlanItem, planItems: MealPlanItem[]): MealPlanItem[] {
  return sortMealItems(
    planItems.filter(
      (candidate) =>
        candidate.id !== item.id &&
        candidate.status === "planned" &&
        !candidate.is_locked &&
        candidate.date >= todayIso(),
    ),
  );
}
