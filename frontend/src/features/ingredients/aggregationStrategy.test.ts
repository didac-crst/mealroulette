import { describe, expect, it } from "vitest";

import { formatAggregationStrategy, formatCatalogLabel } from "./aggregationStrategy";

describe("aggregationStrategy formatters", () => {
  it("formats known aggregation strategies", () => {
    expect(formatAggregationStrategy("prefer_mass")).toBe("Prefer mass");
    expect(formatAggregationStrategy("strict_same_dimension")).toBe("Strict same dimension");
    expect(formatAggregationStrategy(null)).toBe("—");
    expect(formatAggregationStrategy("")).toBe("—");
  });

  it("falls back to catalog label for unknown strategies", () => {
    expect(formatAggregationStrategy("custom_mode")).toBe("Custom mode");
  });

  it("formats catalog labels", () => {
    expect(formatCatalogLabel("food_group")).toBe("Food group");
    expect(formatCatalogLabel(null)).toBe("—");
    expect(formatCatalogLabel(undefined)).toBe("—");
    expect(formatCatalogLabel("  ")).toBe("—");
  });
});
