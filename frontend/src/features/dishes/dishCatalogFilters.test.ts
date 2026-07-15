import { describe, expect, it } from "vitest";

import type { Dish } from "../../api/catalog";

import {
  availableCatalogFilters,
  catalogFilterLabel,
  filterDishesByCatalog,
} from "./dishCatalogFilters";

function dish(partial: Partial<Dish> & Pick<Dish, "id">): Dish {
  return {
    name: `Dish ${partial.id}`,
    course: null,
    meal_composition: "main_dish",
    simple_dish_part: null,
    ...partial,
  } as Dish;
}

const dishes = [
  dish({ id: 1, meal_composition: "main_dish" }),
  dish({ id: 2, meal_composition: "simple_dish", simple_dish_part: "centerpiece" }),
  dish({ id: 3, meal_composition: "simple_dish", simple_dish_part: "sidedish" }),
  dish({ id: 4, meal_composition: "dessert", course: "dessert" }),
];

describe("dishCatalogFilters", () => {
  it("filters dishes by planner role", () => {
    expect(filterDishesByCatalog(dishes, "all")).toHaveLength(4);
    expect(filterDishesByCatalog(dishes, "main_dish").map((item) => item.id)).toEqual([1]);
    expect(filterDishesByCatalog(dishes, "centerpiece").map((item) => item.id)).toEqual([2]);
    expect(filterDishesByCatalog(dishes, "sidedish").map((item) => item.id)).toEqual([3]);
    expect(filterDishesByCatalog(dishes, "dessert").map((item) => item.id)).toEqual([4]);
  });

  it("always exposes All plus composition role chips", () => {
    expect(availableCatalogFilters(dishes)).toEqual([
      "all",
      "main_dish",
      "centerpiece",
      "sidedish",
      "dessert",
    ]);
  });

  it("labels catalog filters", () => {
    expect(catalogFilterLabel("all")).toBe("All");
    expect(catalogFilterLabel("main_dish")).toBe("Main dishes");
    expect(catalogFilterLabel("centerpiece")).toBe("Centerpieces");
    expect(catalogFilterLabel("sidedish")).toBe("Side dishes");
    expect(catalogFilterLabel("dessert")).toBe("Desserts");
  });
});
