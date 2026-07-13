import { describe, expect, it } from "vitest";

import { formatShoppingCategory } from "./formatShoppingCategory";

describe("formatShoppingCategory", () => {
  it("uses mapped labels when available", () => {
    const labels = new Map([["plant_protein", "Plant protein"]]);
    expect(formatShoppingCategory("plant_protein", labels)).toBe("Plant protein");
  });

  it("title-cases unknown category keys", () => {
    expect(formatShoppingCategory("plant_protein")).toBe("Plant Protein");
  });

  it("returns Other for empty or other", () => {
    expect(formatShoppingCategory("")).toBe("Other");
    expect(formatShoppingCategory("other")).toBe("Other");
  });
});
