import { describe, expect, it } from "vitest";

import type { Dish } from "../../api/catalog";

import {
  availableCourseFilters,
  courseFilterLabel,
  filterDishesByCourse,
} from "./dishCatalogFilters";

const dishes = [
  { id: 1, course: "main" },
  { id: 2, course: "starter" },
  { id: 3, course: null },
] as Pick<Dish, "id" | "course">[] as Dish[];

describe("dishCatalogFilters", () => {
  it("filters dishes by course", () => {
    expect(filterDishesByCourse([...dishes], "main")).toHaveLength(1);
    expect(filterDishesByCourse([...dishes], "all")).toHaveLength(3);
  });

  it("returns available course filters", () => {
    expect(availableCourseFilters([...dishes])).toEqual(["all", "main", "starter"]);
  });

  it("labels course filters", () => {
    expect(courseFilterLabel("all")).toBe("All");
    expect(courseFilterLabel("main")).toBe("Main");
  });
});
