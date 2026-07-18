import { describe, expect, it } from "vitest";

import { resolveBreadcrumbs } from "./pageBreadcrumbs";

describe("public catalog breadcrumbs", () => {
  it("resolves catalog browse and review paths", () => {
    expect(resolveBreadcrumbs("/catalog")).toEqual([{ label: "Catalog", to: "/catalog" }]);
    expect(resolveBreadcrumbs("/catalog/requests")).toEqual([
      { label: "Catalog", to: "/catalog" },
      { label: "Publication requests" },
    ]);
    expect(resolveBreadcrumbs("/catalog/review")).toEqual([
      { label: "Catalog", to: "/catalog" },
      { label: "Review" },
    ]);
    expect(resolveBreadcrumbs("/catalog/recipes/abc")).toEqual([
      { label: "Catalog", to: "/catalog" },
      { label: "Recipe" },
    ]);
  });
});
