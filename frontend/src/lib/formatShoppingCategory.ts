export function formatShoppingCategory(category: string, categoryLabels?: Map<string, string>): string {
  const trimmed = category.trim();
  if (!trimmed) {
    return "Other";
  }

  const mapped = categoryLabels?.get(trimmed);
  if (mapped) {
    return mapped;
  }

  if (trimmed.toLowerCase() === "other") {
    return "Other";
  }

  return trimmed
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
