/**
 * Format a stored quantity string for display (does not change stored precision).
 */
export function formatQuantity(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  const raw = typeof value === "number" ? String(value) : value.trim();
  if (!raw) {
    return "";
  }
  const number = Number(raw);
  if (!Number.isFinite(number)) {
    return raw;
  }
  if (Number.isInteger(number)) {
    return String(number);
  }
  const formatted = number.toLocaleString(undefined, {
    maximumFractionDigits: 4,
    useGrouping: false,
  });
  return formatted.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
}

export function formatQuantityWithUnit(
  quantity: string | number | null | undefined,
  unitSymbol?: string | null,
): string {
  const formatted = formatQuantity(quantity);
  if (!formatted) {
    return unitSymbol ?? "";
  }
  return unitSymbol ? `${formatted} ${unitSymbol}` : formatted;
}
