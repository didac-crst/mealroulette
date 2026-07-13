# Meal Composition

## Document metadata

- **Purpose:** `meal_composition` and `simple_dish_part` dish fields for planner slots.
- **Authority:** Canonical for composition semantics; weekly generation rules in [scheduler.md](scheduler.md).
- **Status:** Living — update when composition or planner integration changes.
- **Update when:** Dish model or planner slot logic changes.

---

How a dish participates in lunch/dinner planning. Separate from **`course`** (`starter` | `main` | `dessert`), which describes menu position within a meal.

## Fields

On **`dishes`**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `meal_composition` | `main_dish` \| `simple_dish` \| `dessert` | Yes (default `main_dish`) | Planner slot semantics |
| `simple_dish_part` | `centerpiece` \| `sidedish` | Only when `meal_composition = simple_dish` | Must be NULL otherwise |

Database constraint `ck_dishes_simple_dish_part` enforces the pairing.

Migration `027_dish_meal_composition` backfills `meal_composition = dessert` where `course = dessert`.

## Product semantics

| `meal_composition` | Scheduler (future) | Example |
| --- | --- | --- |
| `main_dish` | One dish fills a lunch/dinner slot | Mushroom risotto |
| `simple_dish` | Two dishes fill a slot (centerpiece + sidedish) | Beans; ham croquettes |
| `dessert` | Manual assign only — excluded from roulette | Fruit crumble |

**`simple_dish_part`** distinguishes the two halves when pairing:

- **`centerpiece`** — primary component of a two-dish slot
- **`sidedish`** — supporting component of a two-dish slot

A lunch/dinner slot is satisfied by either **1× `main_dish`** or **2× `simple_dish`** with one centerpiece and one sidedish (pairing rules TBD).

Desserts may appear on the plan for shopping and review but must not be picked by `generate_week`, `reroll`, or scheduled roulette.

## Out of scope (Phase 11)

- Multi-component `MealPlanItem` rows (one slot, two dishes)
- Scheduler candidate generation and half-meal pairing
- Weekly target counting per slot vs per component

## API

`DishPublic`, create, and update payloads include both fields. Validation:

- `simple_dish` without `simple_dish_part` → 422
- `simple_dish_part` when composition is not `simple_dish` → 422
- Updating composition away from `simple_dish` clears `simple_dish_part`

## Import fixtures

YAML dishes may set `meal_composition` and `simple_dish_part` explicitly. When omitted:

- `course: dessert` → `meal_composition: dessert`
- otherwise → `meal_composition: main_dish`

## Related classification (single source of truth)

| Concern | Source | Editable on dish |
| --- | --- | --- |
| Planner slot role | `meal_composition` (+ `simple_dish_part`) | Yes |
| Fish / meat / pasta / vegetarian weekly targets | Main recipe `computed_traits_json` | No — edit recipe ingredients |
| Soup and other non-derivable styles | Curated `style` tags on dish | Yes (style tags only) |
| Menu course (`starter` / `main` / `dessert`) | Derived from `meal_composition` on save (`dessert` → dessert; otherwise preserved or `main`) | Not shown on dish edit |

Legacy protein/carb dish tags are no longer edited in the UI. The scheduler uses main-recipe computed traits first. When traits are missing, legacy protein/carb tags still act as a **temporary fallback for derivable weekly targets** (fish, meat, pasta, rice, vegetarian) until every dish has a main recipe with ingredients; style tags remain the fallback for non-derivable targets such as soup.

## Related docs

- [BACKLOG.md](../BACKLOG.md) — composable meals follow-up
- [scheduler.md](scheduler.md) — weekly generation (not yet composition-aware)
- [backup-export-import.md](backup-export-import.md) — export must include these dish fields
