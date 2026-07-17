import { describe, expect, it } from "vitest";

import { resolveBreadcrumbs } from "./pageBreadcrumbs";

describe("resolveBreadcrumbs", () => {
  it("returns primary tab crumbs", () => {
    expect(resolveBreadcrumbs("/today")).toEqual([{ label: "Today" }]);
    expect(resolveBreadcrumbs("/plan")).toEqual([{ label: "Plan" }]);
    expect(resolveBreadcrumbs("/shopping")).toEqual([{ label: "Shopping" }]);
  });

  it("returns dish drill-down crumbs with dynamic labels", () => {
    expect(
      resolveBreadcrumbs("/dishes/5", { dishId: "5" }, { dishId: 5, dishName: "Pasta" }),
    ).toEqual([
      { label: "Dishes", to: "/dishes" },
      { label: "Pasta" },
    ]);

    expect(
      resolveBreadcrumbs("/dishes/5/edit", { dishId: "5" }, { dishId: 5, dishName: "Pasta" }),
    ).toEqual([
      { label: "Dishes", to: "/dishes" },
      { label: "Pasta", to: "/dishes/5" },
      { label: "Edit" },
    ]);
  });

  it("returns settings and ingredients trails", () => {
    expect(resolveBreadcrumbs("/settings/targets")).toEqual([
      { label: "Settings", to: "/settings" },
      { label: "Weekly targets" },
    ]);

    expect(resolveBreadcrumbs("/settings/password")).toEqual([
      { label: "Settings", to: "/settings" },
      { label: "Password" },
    ]);

    expect(resolveBreadcrumbs("/settings/members")).toEqual([
      { label: "Settings", to: "/settings" },
      { label: "Household settings" },
    ]);

    expect(
      resolveBreadcrumbs("/ingredients/12/edit", { ingredientId: "12" }, { ingredientId: 12, ingredientName: "Tomato" }),
    ).toEqual([
      { label: "Settings", to: "/settings" },
      { label: "Ingredients", to: "/ingredients" },
      { label: "Tomato", to: "/ingredients/12" },
      { label: "Edit" },
    ]);
  });
});
