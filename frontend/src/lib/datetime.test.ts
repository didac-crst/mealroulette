import { describe, expect, it } from "vitest";

import { formatNowInTimeZone } from "./datetime";

describe("formatNowInTimeZone", () => {
  it("formats without throwing for household timezones", () => {
    const formatted = formatNowInTimeZone("Europe/Paris", new Date("2026-07-12T13:00:00Z"));
    expect(formatted).toContain("2026");
    expect(formatted.length).toBeGreaterThan(10);
  });
});
