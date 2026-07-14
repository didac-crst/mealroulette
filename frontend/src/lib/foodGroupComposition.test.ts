import { describe, expect, it } from "vitest";

import {
  buildCompositionChartData,
  buildDisplayFoodGroupLabels,
  compositionConicGradient,
} from "./foodGroupComposition";

describe("buildCompositionChartData", () => {
  it("groups minor slices into Other", () => {
    const data = buildCompositionChartData({
      carbohydrate: 82,
      cheese: 8,
      vegetable: 6,
      fruit: 4,
    });

    expect(data.hasData).toBe(true);
    expect(data.slices).toEqual([
      { key: "carbohydrate", label: "Carbohydrate", percent: 82 },
      { key: "other", label: "Other", percent: 18 },
    ]);
  });

  it("keeps slices at exactly 10%", () => {
    const data = buildCompositionChartData({
      carbohydrate: 90,
      cheese: 10,
    });

    expect(data.slices).toEqual([
      { key: "carbohydrate", label: "Carbohydrate", percent: 90 },
      { key: "cheese", label: "Cheese", percent: 10 },
    ]);
  });

  it("returns empty data when weights are missing or zero", () => {
    expect(buildCompositionChartData(null)).toEqual({ slices: [], hasData: false });
    expect(buildCompositionChartData({})).toEqual({ slices: [], hasData: false });
  });
});

describe("buildDisplayFoodGroupLabels", () => {
  it("returns readable labels for display metadata", () => {
    expect(
      buildDisplayFoodGroupLabels({
        carbohydrate: 76,
        fruit: 15,
        cheese: 6,
        vegetable: 3,
      }),
    ).toEqual(["Carbohydrate", "Fruit", "Other"]);
  });
});

describe("compositionConicGradient", () => {
  it("builds a conic gradient from slices", () => {
    const gradient = compositionConicGradient(
      [
        { key: "carbohydrate", label: "Carbohydrate", percent: 70 },
        { key: "other", label: "Other", percent: 30 },
      ],
      ["#12b9a5", "#ff7b1a"],
    );

    expect(gradient).toContain("conic-gradient(");
    expect(gradient).toContain("#12b9a5 0% 70%");
    expect(gradient).toContain("#ff7b1a 70% 100%");
  });
});
