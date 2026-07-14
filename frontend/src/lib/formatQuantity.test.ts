import { describe, expect, it } from "vitest";

import { formatQuantity, formatQuantityWithUnit } from "./formatQuantity";

describe("formatQuantity", () => {
  it("strips meaningless trailing zeros", () => {
    expect(formatQuantity("4.0000")).toBe("4");
    expect(formatQuantity("400.0000")).toBe("400");
    expect(formatQuantity("1.5000")).toBe("1.5");
    expect(formatQuantity("0.2500")).toBe("0.25");
  });

  it("handles integers and numbers", () => {
    expect(formatQuantity(12)).toBe("12");
    expect(formatQuantity("0")).toBe("0");
  });

  it("formats with unit", () => {
    expect(formatQuantityWithUnit("500.0000", "g")).toBe("500 g");
    expect(formatQuantityWithUnit(null, "g")).toBe("g");
  });
});
