import { describe, expect, it } from "vitest";

import type { Dish } from "../../api/catalog";
import { dishMatchesSearch, filterDishesBySearch } from "./dishSearch";

const dish = (overrides: Partial<Dish> = {}): Dish => ({
  id: 1,
  public_key: "dish-1",
  name: "Mushroom Risotto",
  description: "Creamy arborio rice with mushrooms",
  default_servings: 4,
  default_prep_time_minutes: null,
  default_cook_time_minutes: null,
  default_difficulty: null,
  course: null,
  status: "active",
  image_url: null,
  suitable_for_lunch: null,
  suitable_for_dinner: null,
  weekday_friendly: null,
  leftovers_possible: null,
  freezer_friendly: null,
  kids_friendly: null,
  thermomix_possible: null,
  active: true,
  notes: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  tag_ids: [],
  computed_traits_json: null,
  seasonality: null,
  ...overrides,
});

describe("dishSearch", () => {
  it("matches dish name tokens case-insensitively", () => {
    expect(dishMatchesSearch(dish(), "mushroom")).toBe(true);
    expect(dishMatchesSearch(dish(), "RISOTTO")).toBe(true);
    expect(dishMatchesSearch(dish(), "mushroom risotto")).toBe(true);
    expect(dishMatchesSearch(dish(), "pasta")).toBe(false);
  });

  it("matches description and recipe variant names", () => {
    expect(dishMatchesSearch(dish(), "creamy")).toBe(true);
    expect(dishMatchesSearch(dish(), "thermomix", ["Thermomix"])).toBe(true);
    expect(dishMatchesSearch(dish(), "standard", ["Standard"])).toBe(true);
  });

  it("requires every token to match somewhere", () => {
    expect(dishMatchesSearch(dish(), "mushroom creamy")).toBe(true);
    expect(dishMatchesSearch(dish(), "mushroom pasta")).toBe(false);
  });

  it("filters a dish list", () => {
    const dishes = [
      dish({ id: 1, name: "Mushroom Risotto" }),
      dish({ id: 2, name: "Tomato Pasta", description: "Quick weeknight pasta" }),
    ];
    expect(filterDishesBySearch(dishes, "")).toHaveLength(2);
    expect(filterDishesBySearch(dishes, "pasta")).toEqual([dishes[1]]);
    expect(filterDishesBySearch(dishes, "mushroom", { 2: ["Mushroom variant"] })).toEqual([
      dishes[0],
      dishes[1],
    ]);
  });
});
