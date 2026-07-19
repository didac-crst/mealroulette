import { describe, expect, it } from "vitest";

import type { PublicRecipeMember } from "../../api/publicCatalog";
import {
  filterPublicCatalogBySearch,
  filterPublicCatalogItems,
  publicCatalogCardMeta,
} from "./publicCatalogDiscovery";

function item(
  overrides: Partial<PublicRecipeMember> & {
    snapshot?: PublicRecipeMember["snapshot"];
  },
): PublicRecipeMember {
  return {
    id: "1",
    status: "public",
    title: "Title",
    description: null,
    current_version: {
      id: "v1",
      version_number: 1,
      published_at: null,
      superseded_at: null,
      created_at: "2026-01-01T00:00:00Z",
    },
    snapshot: {},
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("publicCatalogDiscovery", () => {
  it("filters by title and description", () => {
    const items = [
      item({ id: "1", title: "Public Pasta", description: "Tomato sauce" }),
      item({ id: "2", title: "Green Salad", description: "Fresh greens" }),
    ];
    expect(filterPublicCatalogBySearch(items, "pasta").map((row) => row.id)).toEqual(["1"]);
    expect(filterPublicCatalogBySearch(items, "greens").map((row) => row.id)).toEqual(["2"]);
  });

  it("filters by snapshot meal composition roles", () => {
    const items = [
      item({
        id: "main",
        snapshot: { dish: { meal_composition: "main_dish" } },
      }),
      item({
        id: "side",
        snapshot: { dish: { meal_composition: "simple_dish", simple_dish_part: "sidedish" } },
      }),
      item({
        id: "dessert",
        snapshot: { dish: { meal_composition: "dessert" } },
      }),
    ];
    expect(filterPublicCatalogItems(items, "main").map((row) => row.id)).toEqual(["main"]);
    expect(filterPublicCatalogItems(items, "sides").map((row) => row.id)).toEqual(["side"]);
    expect(filterPublicCatalogItems(items, "desserts").map((row) => row.id)).toEqual(["dessert"]);
  });

  it("builds card metadata from snapshot fields", () => {
    expect(
      publicCatalogCardMeta(
        item({
          snapshot: {
            dish: { meal_composition: "main_dish", course: "main" },
            recipe: { servings: 4 },
          },
        }),
      ),
    ).toBe("Main · Main · 4 servings");
  });
});
