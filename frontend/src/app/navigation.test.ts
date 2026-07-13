import { describe, expect, it } from "vitest";

import { isNavActive, PRIMARY_NAV } from "./navigation";

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

  it("detects active routes including nested paths", () => {
    expect(isNavActive("/dishes/42", "/dishes")).toBe(true);
    expect(isNavActive("/plan", "/plan")).toBe(true);
    expect(isNavActive("/review", "/plan")).toBe(false);
  });
});
