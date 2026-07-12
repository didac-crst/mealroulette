import { describe, expect, it } from "vitest";

import { targetHint, targetLabel } from "./planningTargetLabels";

describe("planningTargetLabels", () => {
  it("labels known presets", () => {
    expect(targetLabel("fish")).toBe("Fish");
    expect(targetLabel("meat")).toBe("Meat");
  });

  it("falls back for custom keys", () => {
    expect(targetLabel("noodles")).toBe("noodles");
  });

  it("provides hints for presets", () => {
    expect(targetHint("fish")).toContain("tagged");
    expect(targetHint("unknown")).toBeNull();
  });
});
