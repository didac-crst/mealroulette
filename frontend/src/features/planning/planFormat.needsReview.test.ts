import { describe, expect, it } from "vitest";

import { formatNeedsReviewCount } from "./planFormat";

describe("formatNeedsReviewCount", () => {
  it("uses singular grammar for one meal", () => {
    expect(formatNeedsReviewCount(1)).toBe("1 meal needs review");
  });

  it("uses plural grammar for multiple meals", () => {
    expect(formatNeedsReviewCount(3)).toBe("3 meals need review");
  });
});
