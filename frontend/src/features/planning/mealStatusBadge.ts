import type { MealPlanItem } from "../../api/planning";
import type { StatusBadgeVariant } from "../../components/ui";

import { isFutureMealDate } from "./planFormat";

export function mealStatusBadgeVariant(
  item: MealPlanItem,
  mode: "plan" | "review" | "today",
): StatusBadgeVariant {
  if ((mode === "review" || mode === "today") && item.status === "planned" && !isFutureMealDate(item.date)) {
    return "warning";
  }

  if (item.manually_selected && item.status === "planned") {
    return "info";
  }

  switch (item.status) {
    case "eaten":
    case "ate_leftovers":
      return "success";
    case "skipped":
      return "muted";
    case "planned":
      return item.is_locked ? "info" : "default";
    default:
      return "default";
  }
}
