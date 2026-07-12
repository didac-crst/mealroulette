import { describe, expect, it } from "vitest";

import { formatNowInTimeZone, todayIsoInTimeZone } from "./datetime";

describe("formatNowInTimeZone", () => {
  it("formats without throwing for household timezones", () => {
    const formatted = formatNowInTimeZone("Europe/Paris", new Date("2026-07-12T13:00:00Z"));
    expect(formatted).toContain("2026");
    expect(formatted.length).toBeGreaterThan(10);
  });
});

describe("todayIsoInTimeZone", () => {
  it("returns YYYY-MM-DD in the requested timezone", () => {
    expect(todayIsoInTimeZone("Europe/Paris", new Date("2026-07-12T22:30:00Z"))).toBe("2026-07-13");
    expect(todayIsoInTimeZone("Pacific/Honolulu", new Date("2026-07-12T22:30:00Z"))).toBe("2026-07-12");
  });
});
