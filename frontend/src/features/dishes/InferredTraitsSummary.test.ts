import { describe, expect, it } from "vitest";

import { buildInferredTraitItems } from "./InferredTraitsSummary";

describe("buildInferredTraitItems", () => {
  it("returns empty list for null or undefined traits", () => {
    expect(buildInferredTraitItems(null)).toEqual([]);
    expect(buildInferredTraitItems(undefined)).toEqual([]);
  });

  it("prefers food group weights over contains_food_groups", () => {
    const items = buildInferredTraitItems({
      food_group_weights: { carbohydrate: 60, vegetable: 40 },
      contains_food_groups: ["fruit"],
      vegan: true,
      carb_heavy: true,
    });

    expect(items.find((item) => item.label === "Food groups")?.value).toBe("Carbohydrate, Vegetable");
    expect(items.find((item) => item.label === "Diet")?.value).toBe("Vegan · carb-heavy");
  });

  it("falls back to contains_food_groups when weights are missing", () => {
    const items = buildInferredTraitItems({
      contains_food_groups: ["fish", "vegetable"],
      vegan: false,
    });

    expect(items.find((item) => item.label === "Food groups")?.value).toBe("fish, vegetable");
    expect(items.find((item) => item.label === "Diet")?.value).toBe("Not vegan");
  });

  it("includes dominant protein and carb when present", () => {
    const items = buildInferredTraitItems({
      food_group_weights: { meat: 55, carbohydrate: 45 },
      dominant_protein: "chicken_family",
      dominant_carb: "rice_family",
      vegan: false,
      carb_heavy: false,
    });

    expect(items.find((item) => item.label === "Dominant protein")?.value).toBe("chicken family");
    expect(items.find((item) => item.label === "Dominant carb")?.value).toBe("rice family");
  });

  it("omits diet when no displayable traits exist", () => {
    expect(buildInferredTraitItems({ vegan: true, carb_heavy: false })).toEqual([]);
  });
});
