import { describe, expect, it } from "vitest";

import {
  ADMIN_NAV,
  householdPrimaryNav,
  isNavActive,
  PLATFORM_NAV,
  PRIMARY_NAV,
  SETTINGS_NAV,
} from "./navigation";

describe("navigation", () => {
  it("lists Shopping with five primary tabs", () => {
    expect(PRIMARY_NAV).toHaveLength(5);
    expect(PRIMARY_NAV.map((item) => item.label)).toEqual([
      "Today",
      "Plan",
      "Review",
      "Shopping",
      "Dishes",
    ]);
  });

  it("adds Ingredients for household admins", () => {
    expect(householdPrimaryNav(false)).toEqual(PRIMARY_NAV);
    expect(householdPrimaryNav(true).map((item) => item.label)).toEqual([
      "Today",
      "Plan",
      "Review",
      "Shopping",
      "Dishes",
      "Ingredients",
    ]);
  });

  it("exposes platform-only ingredients nav", () => {
    expect(PLATFORM_NAV.map((item) => item.label)).toEqual(["Ingredients"]);
  });

  it("keeps ADMIN_NAV as a SETTINGS_NAV alias", () => {
    expect(ADMIN_NAV).toBe(SETTINGS_NAV);
  });

  it("detects active routes including nested paths", () => {
    expect(isNavActive("/dishes/42", "/dishes")).toBe(true);
    expect(isNavActive("/plan", "/plan")).toBe(true);
    expect(isNavActive("/review", "/plan")).toBe(false);
  });
});
