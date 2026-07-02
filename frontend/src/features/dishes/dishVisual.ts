import type { Dish } from "../../api/catalog";
import { COURSE_OPTIONS, formatOptionLabel } from "./classification";
import { formatDifficulty } from "./constants";

const COURSE_EMOJI: Record<string, string> = {
  starter: "🥣",
  main: "🍽️",
  dessert: "🍰",
};

export function dishPlaceholderEmoji(dish: Pick<Dish, "course" | "name">): string {
  if (dish.course && COURSE_EMOJI[dish.course]) {
    return COURSE_EMOJI[dish.course];
  }
  return "🍲";
}

export function dishCardMeta(dish: Dish): string {
  const parts = [
    formatOptionLabel(COURSE_OPTIONS, dish.course ?? ""),
    formatDifficulty(dish.default_difficulty),
  ].filter((part) => part !== "Not set");
  return parts.join(" · ") || "No details yet";
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trimEnd()}…`;
}
