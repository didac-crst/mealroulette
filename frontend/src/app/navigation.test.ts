import { describe, expect, it } from "vitest";

import {
  ADMIN_NAV,
  householdPrimaryNav,
  isNavActive,
  PLATFORM_NAV,
  PRIMARY_NAV,
  SETTINGS_NAV,
  resolvePrimaryNav,
} from "./navigation";

describe("navigation", () => {
  it("lists Shopping with six primary tabs", () => {
    expect(PRIMARY_NAV).toHaveLength(6);
    expect(PRIMARY_NAV.map((item) => item.label)).toEqual([
      "Today",
      "Plan",
      "Review",
      "Shopping",
      "Dishes",
      "Catalog",
    ]);
  });

  it("adds Ingredients for household members and admins", () => {
    expect(householdPrimaryNav(false)).toEqual(PRIMARY_NAV);
    expect(householdPrimaryNav(true).map((item) => item.label)).toEqual([
      "Today",
      "Plan",
      "Review",
      "Shopping",
      "Dishes",
      "Catalog",
      "Ingredients",
    ]);
  });

  it("exposes platform-only ingredients and recipe review nav", () => {
    expect(PLATFORM_NAV.map((item) => item.label)).toEqual(["Ingredients", "Recipe review"]);
  });

  it("resolves primary nav by household and role", () => {
    expect(
      resolvePrimaryNav({ hasHousehold: false, isPlatformAdmin: true, isHouseholdAdmin: false }).map(
        (item) => item.label,
      ),
    ).toEqual(["Ingredients", "Recipe review"]);

    expect(
      resolvePrimaryNav({ hasHousehold: false, isPlatformAdmin: false, isHouseholdAdmin: false }),
    ).toEqual([]);

    expect(
      resolvePrimaryNav({ hasHousehold: true, isPlatformAdmin: false, isHouseholdAdmin: false }).map(
        (item) => item.label,
      ),
    ).toEqual(["Today", "Plan", "Review", "Shopping", "Dishes", "Catalog", "Ingredients"]);

    expect(
      resolvePrimaryNav({ hasHousehold: true, isPlatformAdmin: true, isHouseholdAdmin: false }).map(
        (item) => item.label,
      ),
    ).toEqual([
      "Today",
      "Plan",
      "Review",
      "Shopping",
      "Dishes",
      "Catalog",
      "Ingredients",
      "Recipe review",
    ]);

    expect(
      resolvePrimaryNav({ hasHousehold: true, isPlatformAdmin: false, isHouseholdAdmin: true }).map(
        (item) => item.label,
      ),
    ).toContain("Ingredients");
  });

  it("keeps ADMIN_NAV as a SETTINGS_NAV alias", () => {
    expect(ADMIN_NAV).toBe(SETTINGS_NAV);
  });

  it("detects active routes including nested paths", () => {
    expect(isNavActive("/dishes/42", "/dishes")).toBe(true);
    expect(isNavActive("/plan", "/plan")).toBe(true);
    expect(isNavActive("/review", "/plan")).toBe(false);
    expect(isNavActive("/catalog/review", "/catalog")).toBe(false);
    expect(isNavActive("/catalog/recipes/abc", "/catalog")).toBe(true);
    expect(isNavActive("/catalog/requests", "/catalog")).toBe(true);
    expect(isNavActive("/catalog/review", "/catalog/review")).toBe(true);
  });
});
