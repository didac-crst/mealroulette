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

    expect(resolveBreadcrumbs("/ingredients")).toEqual([{ label: "Ingredients", to: "/ingredients" }]);
    expect(resolveBreadcrumbs("/ingredients/proposals")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Proposals" },
    ]);
    expect(resolveBreadcrumbs("/ingredients/proposal-review")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Proposal review" },
    ]);

    expect(resolveBreadcrumbs("/settings/my-ingredient-proposals")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Ingredient proposals", to: "/ingredients/proposals" },
    ]);

    expect(resolveBreadcrumbs("/settings/ingredient-proposals")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Proposal review", to: "/ingredients/proposal-review" },
    ]);

    expect(resolveBreadcrumbs("/settings/ingredient-proposals/abc")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Proposal review", to: "/ingredients/proposal-review" },
    ]);

    expect(resolveBreadcrumbs("/ingredients/proposal-review/p1")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Proposal review", to: "/ingredients/proposal-review" },
      { label: "Proposal" },
    ]);

    expect(resolveBreadcrumbs("/ingredients/taxonomy")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Taxonomy" },
    ]);

    expect(resolveBreadcrumbs("/ingredients/new")).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "New ingredient" },
    ]);

    expect(
      resolveBreadcrumbs("/ingredients/12", { ingredientId: "12" }, { ingredientId: 12, ingredientName: "Tomato" }),
    ).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Tomato" },
    ]);

    expect(
      resolveBreadcrumbs("/ingredients/12/edit", { ingredientId: "12" }, { ingredientId: 12, ingredientName: "Tomato" }),
    ).toEqual([
      { label: "Ingredients", to: "/ingredients" },
      { label: "Tomato", to: "/ingredients/12" },
      { label: "Edit" },
    ]);
  });
});
