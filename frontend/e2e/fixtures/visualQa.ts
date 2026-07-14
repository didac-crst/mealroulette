import type { BrowserContext, Page, Route } from "@playwright/test";

const TIMESTAMP = "2026-01-01T00:00:00Z";

const ADMIN_USER = {
  id: 1,
  username: "admin",
  email: "admin@test.local",
  role: "admin",
  active: true,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP,
};

const SCHEDULER_SETTINGS = {
  enabled: true,
  run_weekday: 4,
  run_time: "18:00",
  timezone: "Europe/Paris",
  target_week_offset: 1,
  notify_telegram: true,
  notify_planning_days: 7,
  last_roulette_at: null,
  last_error: null,
};

const DISH = {
  id: 1,
  public_key: "dish-1",
  name: "Gebratener Lachs mit Ofengemüse",
  description: "Wöchentliches Familiengericht mit saisonalem Gemüse",
  default_servings: 4,
  default_prep_time_minutes: 15,
  default_cook_time_minutes: 25,
  default_difficulty: "medium",
  course: "main",
  meal_composition: "main_dish",
  simple_dish_part: null,
  status: "active",
  image_url: null,
  suitable_for_lunch: null,
  suitable_for_dinner: true,
  weekday_friendly: true,
  leftovers_possible: true,
  freezer_friendly: null,
  kids_friendly: null,
  thermomix_possible: null,
  active: true,
  notes: null,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP,
  tag_ids: [],
  computed_traits_json: null,
  seasonality: null,
};

const INGREDIENT = {
  id: 1,
  canonical_name: "cherry_tomato",
  display_name: "Kirschtomaten",
  category: "produce",
  food_group: "vegetable",
  family: "tomato_family",
  default_unit_id: 1,
  default_dimension: "mass",
  preferred_shopping_unit_id: 1,
  aggregation_unit_id: 1,
  aggregation_strategy: null,
  pantry_item: false,
  season_start_month: null,
  season_end_month: null,
  notes: null,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP,
};

const UNITS = [{ id: 1, symbol: "g", dimension: "mass", name: "gram" }];

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoWeekStartMonday(reference = new Date()): string {
  const date = new Date(reference);
  const weekday = date.getDay();
  const diff = weekday === 0 ? -6 : 1 - weekday;
  date.setDate(date.getDate() + diff);
  return date.toISOString().slice(0, 10);
}

function addDays(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T12:00:00`);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function mealPlanItem(
  id: number,
  date: string,
  mealSlot: "lunch" | "dinner",
  status: "planned" | "eaten" | "skipped" | "ate_leftovers" = "planned",
  reviewed = false,
) {
  return {
    id,
    meal_plan_id: 1,
    date,
    meal_slot: mealSlot,
    dish_id: 1,
    recipe_id: 1,
    dish_name: "Gebratener Lachs mit langem Gerichtsnamen",
    recipe_variant_name: "Standard",
    status,
    is_locked: false,
    manually_selected: false,
    skip_reason: null,
    skip_comment: null,
    leftover_source_item_id: null,
    selection_reasons_json: null,
    computed_traits_json: null,
    review_saved_at: reviewed ? TIMESTAMP : null,
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP,
  };
}

function buildMealPlan() {
  const today = isoToday();
  const weekStart = isoWeekStartMonday();
  return {
    id: 1,
    week_start_date: weekStart,
    status: "active",
    items: [
      mealPlanItem(1, today, "lunch", "eaten", true),
      mealPlanItem(2, today, "dinner"),
      mealPlanItem(3, addDays(today, 1), "lunch"),
    ],
    roulette_undo_available: false,
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP,
  };
}

function buildShoppingList() {
  const today = isoToday();
  return {
    id: null,
    from_date: today,
    to_date: addDays(today, 2),
    status: "draft",
    exclude_pantry: true,
    items: [
      {
        id: null,
        ingredient_id: 1,
        display_name: "Kirschtomaten",
        quantity: "400",
        unit_id: 1,
        unit_symbol: "g",
        category: "produce",
        checked: false,
        approximate: false,
        optional: false,
        source_meal_plan_item_ids: [1],
        source_contributions: [],
        raw_components: [],
      },
    ],
    planned_meals: [
      {
        meal_plan_item_id: 1,
        date: today,
        meal_slot: "lunch",
        dish_name: "Gebratener Lachs mit langem Gerichtsnamen",
        recipe_variant_name: "Standard",
      },
    ],
  };
}

function fulfillJson(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export async function installVisualQaSession(context: BrowserContext) {
  await context.addInitScript(() => {
    localStorage.setItem("mealroulette_access_token", "visual-qa-token");
    localStorage.setItem("mealroulette_refresh_token", "visual-qa-refresh");
  });
}

async function handleApiRoute(route: Route) {
  const url = new URL(route.request().url());
  const path = url.pathname;

  if (path === "/api/auth/me") {
    return fulfillJson(route, ADMIN_USER);
  }
  if (path === "/api/auth/refresh") {
    return fulfillJson(route, {
      access_token: "visual-qa-token",
      refresh_token: "visual-qa-refresh",
      token_type: "bearer",
    });
  }
  if (path === "/api/meal-plans/current" || /^\/api\/meal-plans\/\d{4}-\d{2}-\d{2}$/.test(path)) {
    return fulfillJson(route, buildMealPlan());
  }
  if (path.startsWith("/api/meal-history")) {
    return fulfillJson(route, []);
  }
  if (/^\/api\/meal-plan-items\/\d+\/rating$/.test(path)) {
    return fulfillJson(route, {
      id: 1,
      meal_plan_item_id: 1,
      dish_id: 1,
      recipe_id: 1,
      rating: 4,
      comment: "Very good, but use less salt next time",
      created_at: TIMESTAMP,
    });
  }
  if (path.startsWith("/api/shopping-list")) {
    return fulfillJson(route, buildShoppingList());
  }
  if (path === "/api/dishes") {
    return fulfillJson(route, [DISH]);
  }
  if (path.startsWith("/api/dishes/") && path.endsWith("/recipes")) {
    return fulfillJson(route, [{ id: 1, dish_id: 1, variant_name: "Standard", is_main: true }]);
  }
  if (path.startsWith("/api/dishes/")) {
    return fulfillJson(route, DISH);
  }
  if (path === "/api/ingredients") {
    return fulfillJson(route, [INGREDIENT]);
  }
  if (path.startsWith("/api/ingredients/")) {
    return fulfillJson(route, { ...INGREDIENT, aliases: [], unit_conversions: [] });
  }
  if (path === "/api/ingredient-categories") {
    return fulfillJson(route, [{ id: "produce", label: "Obst und Gemüse" }]);
  }
  if (path === "/api/units") {
    return fulfillJson(route, UNITS);
  }
  if (path === "/api/tags") {
    return fulfillJson(route, []);
  }
  if (path.startsWith("/api/scheduler")) {
    return fulfillJson(route, SCHEDULER_SETTINGS);
  }
  if (path.includes("/recipes") && !path.startsWith("/api/dishes/")) {
    return fulfillJson(route, { id: 1, dish_id: 1, variant_name: "Standard", is_main: true });
  }
  if (path === "/api/health" || path === "/api/health/ready") {
    return fulfillJson(route, { status: "ok" });
  }

  if (route.request().method() === "GET") {
    return fulfillJson(route, []);
  }
  return fulfillJson(route, {});
}

export async function setupVisualQaApiMocks(context: BrowserContext) {
  await context.route(/\/api\//, handleApiRoute);
}

export async function assertNoHorizontalOverflow(page: Page) {
  const result = await page.evaluate(() => {
    const root = document.documentElement;
    const offenders: Array<{ tag: string; className: string; right: number }> = [];
    for (const element of document.querySelectorAll("*")) {
      const rect = element.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) {
        continue;
      }
      if (rect.right > root.clientWidth + 1) {
        offenders.push({
          tag: element.tagName.toLowerCase(),
          className: typeof element.className === "string" ? element.className : "",
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          width: Math.round(rect.width),
        });
      }
    }
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      offenders: offenders.slice(0, 5),
    };
  });
  if (result.scrollWidth > result.clientWidth + 1) {
    const details = result.offenders
      .map((entry) => `${entry.tag}.${entry.className} (l=${entry.left}, w=${entry.width}, r=${entry.right})`)
      .join("; ");
    throw new Error(
      `Page has horizontal overflow (${result.scrollWidth}px > ${result.clientWidth}px)${details ? `: ${details}` : ""}`,
    );
  }
}

export const VISUAL_QA_ROUTES = [
  { path: "/today", heading: "Today" },
  { path: "/plan", heading: "Plan" },
  { path: "/review", heading: "Review" },
  { path: "/shopping", heading: "Shopping" },
  { path: "/dishes", heading: "Dishes" },
  { path: "/settings", heading: "Settings" },
  { path: "/ingredients", heading: "Ingredients" },
] as const;
