import type { Dish } from "../../api/catalog";
import { COURSE_OPTIONS } from "./classification";

export type DishCourseFilter = "all" | NonNullable<Dish["course"]>;

export function filterDishesByCourse(dishes: Dish[], courseFilter: DishCourseFilter): Dish[] {
  if (courseFilter === "all") {
    return dishes;
  }
  return dishes.filter((dish) => dish.course === courseFilter);
}

export function availableCourseFilters(dishes: Dish[]): DishCourseFilter[] {
  const filters = new Set<DishCourseFilter>(["all"]);
  for (const dish of dishes) {
    if (dish.course) {
      filters.add(dish.course);
    }
  }
  return Array.from(filters);
}

export function courseFilterLabel(filter: DishCourseFilter): string {
  if (filter === "all") {
    return "All";
  }
  return COURSE_OPTIONS.find((option) => option.value === filter)?.label ?? filter;
}
