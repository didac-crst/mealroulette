# Composable Meals and Simple Dishes

## Purpose

Implement meal slots that can contain multiple dishes, so a planned lunch/dinner can be:

- one roulette-selected `main_dish`;
- one roulette-selected simple pair: `centerpiece + sidedish`;
- any number of manually added extras: desserts, sides, additional mains, starters, or other simple dishes;
- explicitly marked as `Do not plan`, so roulette does not fill it.

This is a planning semantics change, not just a UI change.

Use the current branch/main state after `v0.9.0`.

## Feasibility Assessment

### Feasible

The requested behavior is feasible, but it requires:

- a database migration;
- API schema changes;
- scheduler/generator changes;
- planning UI restructuring;
- shopping aggregation changes;
- review/history/title formatting changes;
- analytics/composition aggregation additions.

### Current Constraint

Current model:

```text
meal_plan_items
  unique(meal_plan_id, date, meal_slot)
  dish_id
  recipe_id
  manually_selected
  selection_reasons_json
```

This means one meal slot can hold only one dish. The unique constraint on `{meal_plan_id, date, meal_slot}` is correct for the slot/container, but `dish_id` and `recipe_id` do not belong directly on that container once multiple dishes are allowed.

### No Product Contradiction

The product idea is internally coherent if we separate:

- **meal slot**: lunch/dinner on a date, with execution/review state and optional `do_not_plan`;
- **meal dish line**: one dish/recipe inside that slot, with role, source, order, and optional roulette reasons.

### Main Risk

Trying to retrofit multiple dishes directly into `meal_plan_items` would create confused semantics. Do not add `dish_id_2`, JSON arrays, or overload `skip` as "do not plan".

Recommended design: keep `meal_plan_items` as the slot container and add a child table for dish lines.

---

## Product Semantics

## Meal Slot

A meal slot is one `{meal_plan_id, date, meal_slot}` container.

It has:

- date and lunch/dinner slot;
- execution state (`planned`, `eaten`, `skipped`, `ate_leftovers`);
- lock state;
- review state;
- optional `do_not_plan` state;
- zero or more dish lines.

The slot exists even when no dish is assigned.

## Meal Dish Line

A meal dish line is one dish/recipe assigned to a meal slot.

Each line has:

- dish;
- recipe variant;
- display position;
- role;
- source;
- optional roulette selection reasons.

Roles:

```text
main
centerpiece
side
dessert
extra
```

Source:

```text
roulette
manual
leftover
```

For MVP, `leftover` source may remain represented at the slot status level if implementing line-level leftovers is too large. Do not fake line-level leftovers unless fully implemented.

## Automatic Roulette Semantics

Roulette fills only eligible empty slots or slots whose roulette package is being rerolled.

For each eligible slot, roulette may assign either:

1. one `main_dish`; or
2. one simple pair:
   - one `simple_dish` with `simple_dish_part = centerpiece`;
   - one `simple_dish` with `simple_dish_part = sidedish`.

Roulette must not select:

- desserts;
- manual extras;
- slots marked `do_not_plan`;
- locked slots;
- past slots;
- slots with execution state other than `planned`.

Roulette-created lines must use:

```text
source = roulette
```

Manual additions must use:

```text
source = manual
```

Selection reasons belong to roulette lines or to the roulette package. Manual lines should not show "Why this meal?" unless there are explicit manual notes in a future feature.

## Manual Additions

Users can add any number of dish lines to a meal slot after it has an assignment.

Examples:

- add dessert to a generated main dish;
- add side dish to a generated main dish;
- add a second main;
- add starter;
- add side before the main is chosen;
- add extra dishes to a simple pair.

Manual additions do not make the slot ineligible for review/shopping. They are part of the meal.

## Do Not Plan

Do not use "clear assignment" as the product concept.

There are two different actions:

1. **Remove line** — delete an existing dish line.
2. **Do not plan** — mark the whole slot as intentionally unavailable, such as eating outside.

`Do not plan` behavior:

- prevents generate week, reroll, and scheduled roulette from assigning anything to the slot;
- removes existing roulette lines only after explicit confirmation;
- may either keep or remove manual lines depending on user choice; default should remove all lines for clarity;
- excludes the slot from shopping;
- displays as `Not planning`;
- is distinct from `skipped`, which is an after-the-fact execution/review outcome.

Recommended slot field:

```text
planning_state = open | do_not_plan
```

Do not overload `MealPlanItemStatus.skipped`.

## Titles

Current UI assumes one dish title per meal. New title logic:

### Compact card title

If no lines:

```text
Unassigned
```

If `do_not_plan`:

```text
Not planning
```

If one line:

```text
{Dish name}
```

If exactly two roulette simple lines (`centerpiece + side`):

```text
{Centerpiece dish} with {Side dish}
```

If multiple lines:

```text
{Primary dish} + {N} more
```

Primary dish order:

1. roulette `main`;
2. roulette `centerpiece`;
3. manual `main`;
4. manual `centerpiece`;
5. first line by position.

### Expanded meal view

Show every line, grouped or ordered by position, with source and role badges:

```text
Pasta alla Norma                         Roulette · Main
Green salad                              Manual · Side
Fruit crumble                            Manual · Dessert
```

## From Dish Detail / Catalog "Plan For..."

Do not silently replace an existing assignment.

When planning a dish from the catalog:

- If target slot is empty and not `do_not_plan`, add the dish as a manual line.
- If target slot has existing lines, default action should be **Add to meal**.
- Offer **Replace roulette selection** only when the target slot has roulette lines.
- Offer **Replace selected line** only in a line-specific context.
- Do not replace manual lines without explicit user choice.

Recommended Plan For dialog behavior:

```text
Choose date/slot
Mode:
  Add to meal
  Replace roulette selection   (only enabled when roulette lines exist)
  Replace selected line        (only from a line context)
```

MVP can implement only **Add to meal** from dish pages, as long as it is explicit.

## Add-Line UI

Default meal card should show one assignment surface when empty.

After a dish is selected, show a visible non-disabled `+ Add dish` button below the existing line(s).

Recommended add-line interaction:

- `+ Add dish` opens an inline row or bottom sheet.
- Provide a filter segmented control:

```text
All | Main | Centerpiece | Side | Dessert
```

- Default filter:
  - empty slot: `All` or `Main`;
  - slot has centerpiece but no side: suggest `Side`;
  - slot has side but no centerpiece/main: suggest `Centerpiece`;
  - slot has main: suggest `Side` or `Dessert`, but keep `All` available.

Every line has:

- dish selector;
- recipe variant selector when needed;
- role display or selector;
- source badge (`Roulette` or `Manual`);
- remove button.

Remove button rules:

- manual line: remove immediately after confirmation only if destructive enough; otherwise direct remove with undo toast is OK;
- roulette line: removing it converts the slot to manual/custom state or removes the roulette package. Make this explicit.

Avoid an empty dropdown row as a clearing mechanism.

## Review Semantics

MVP recommendation:

- Review/rating applies to the whole meal slot, not individual dish lines.
- Status actions (`eaten`, `skipped`, `ate_leftovers`) apply to the whole meal.
- Review UI displays all dish lines in the meal.
- Rating comments can mention individual dishes, but data model remains slot-level.

Future extension:

- line-level ratings for side dishes or dessert.

Do not implement line-level ratings in the initial composable-meals release unless explicitly approved.

## Leftovers Semantics

MVP recommendation:

- Keep leftovers slot-level.
- If a composed meal is marked leftovers, it references the source meal slot.
- Shopping excludes leftover slots as today.

Future extension:

- line-level leftovers, e.g. "eat leftover rice but cook fresh fish".

Do not implement line-level leftovers in the initial composable-meals release.

---

## Backend Design

## Database Migration

Add table:

```text
meal_plan_item_dishes
```

Suggested columns:

```text
id                       pk
meal_plan_item_id         fk meal_plan_items.id on delete cascade, indexed
dish_id                   fk dishes.id on delete set null
recipe_id                 fk recipes.id on delete set null
position                  integer not null
role                      enum/string: main | centerpiece | side | dessert | extra
source                    enum/string: roulette | manual | leftover
selection_reasons_json    jsonb nullable
created_at                timestamp
updated_at                timestamp
```

Recommended constraints:

- unique `(meal_plan_item_id, position)`;
- `position >= 0`;
- `dish_id` nullable only for historical/deleted dish compatibility, same as current `MealPlanItem.dish_id`;
- `recipe_id` must belong to `dish_id` when both exist; enforce in service if DB constraint is cumbersome.

Add to `meal_plan_items`:

```text
planning_state: open | do_not_plan
```

Default:

```text
open
```

Backfill:

- For every existing `meal_plan_items` row with `dish_id is not null`, create one `meal_plan_item_dishes` row:
  - `position = 0`;
  - `dish_id = meal_plan_items.dish_id`;
  - `recipe_id = meal_plan_items.recipe_id`;
  - `source = manual` if `manually_selected = true`, else `roulette`;
  - `role` derived from dish:
    - `meal_composition = main_dish` -> `main`;
    - `meal_composition = dessert` -> `dessert`;
    - `simple_dish_part = centerpiece` -> `centerpiece`;
    - `simple_dish_part = sidedish` -> `side`;
    - fallback -> `main`;
  - `selection_reasons_json = meal_plan_items.selection_reasons_json`.

Compatibility:

- Keep existing `meal_plan_items.dish_id`, `recipe_id`, `manually_selected`, and `selection_reasons_json` for this phase if removal is too risky.
- Treat them as legacy/primary-line mirrors only.
- New API responses should use line data.
- Update mirrors from primary line for backward compatibility.

Future cleanup:

- Remove or fully deprecate direct dish fields from `meal_plan_items` after all services use lines.

## API Schemas

Add:

```python
class MealPlanDishLinePublic(BaseModel):
    id: int
    meal_plan_item_id: int
    dish_id: int | None
    recipe_id: int | None
    dish_name: str | None
    recipe_variant_name: str | None
    role: str
    source: str
    position: int
    selection_reasons_json: dict | None
    computed_traits_json: dict | None
```

Extend:

```python
class MealPlanItemPublic:
    planning_state: str
    lines: list[MealPlanDishLinePublic]
    title: str
    computed_traits_json: dict | None
```

`computed_traits_json` on the item should represent aggregate meal composition, not only the primary line.

Keep existing fields temporarily:

```text
dish_id
recipe_id
dish_name
recipe_variant_name
manually_selected
selection_reasons_json
```

They should map to the primary line for old frontend consumers until cleanup.

## API Endpoints

Add line endpoints:

```http
POST /api/meal-plan-items/{item_id}/lines
PUT /api/meal-plan-item-lines/{line_id}
DELETE /api/meal-plan-item-lines/{line_id}
POST /api/meal-plan-items/{item_id}/do-not-plan
POST /api/meal-plan-items/{item_id}/reopen
```

Request examples:

```json
{
  "dish_id": 12,
  "recipe_id": 30,
  "role": "side",
  "position": 1
}
```

```json
{
  "remove_existing_lines": true
}
```

Update existing:

```http
POST /api/meal-plan-items/assign
```

Current behavior replaces a slot. New behavior should be explicit:

```json
{
  "date": "2026-07-14",
  "meal_slot": "dinner",
  "dish_id": 12,
  "recipe_id": 30,
  "mode": "add" | "replace_roulette" | "replace_all"
}
```

Default for backwards compatibility:

```text
replace_all
```

But frontend should use explicit `add` for catalog Plan For flows.

## Scheduler

### Candidate model

Extend `DishCandidate` with:

```text
meal_composition
simple_dish_part
```

Split candidates:

- main candidates: `meal_composition = main_dish`;
- centerpiece candidates: `meal_composition = simple_dish AND simple_dish_part = centerpiece`;
- side candidates: `meal_composition = simple_dish AND simple_dish_part = sidedish`;
- desserts excluded from roulette.

### Generation package

Replace one-dish `SlotAssignment` semantics with a package:

```python
class SlotAssignment:
    item_id: int
    lines: list[SlotAssignmentLine]
    score: float
    selection_reasons_json: dict

class SlotAssignmentLine:
    dish_id: int
    recipe_id: int
    role: str
    position: int
    selection_reasons_json: dict | None
```

For MVP, each slot assignment package is either:

- one main line; or
- two simple lines: centerpiece + side.

### Scoring simple pairs

Simple first implementation:

- score the centerpiece as the primary candidate;
- score side compatibility with a smaller modifier;
- aggregate pair vector for similarity and weekly target counting.

**Current generator behaviour (performance guard):**

- eligible centerpieces and sides are **pre-scored once per slot**;
- pair total = `centerpiece_score + 0.25 × side_score` using those pre-scored estimates;
- sides are **not** rescored with the centerpiece already in `assigned_dish_ids`, and the pair is **not** yet scored as a combined package (aggregate traits/vector/target contribution). This is an acceptable approximation for interactive latency; longer term, score pairs as one unit per the bullets above.
- large simple-dish catalogs use a **bounded shortlist** (top scorers plus a random sample from the remainder) and **adaptive `plan_attempts`** — see [scheduler.md](scheduler.md) § Sequential week generation.

Pair vector options:

1. compute aggregate from the two recipes' ingredient grams; preferred;
2. approximate by averaging normalized vectors weighted by total recipe reference grams.

Do not average normalized percentages equally unless there is no better option.

### Fixed assignments

For similarity and weekly targets, fixed/manual meals should be represented as aggregate meal packages, not only one dish ID.

MVP acceptable shortcut:

- primary line drives weekly target counting;
- aggregate vector drives similarity if easy;
- document any shortcut clearly.

Recommended:

- aggregate all non-`do_not_plan` lines in a slot for similarity;
- count weekly targets once per meal slot using aggregate meal traits, not once per line, unless future product decision says otherwise.

### Reroll

Reroll behavior:

- reroll replaces roulette-sourced lines in the slot;
- manual lines remain;
- `do_not_plan` slots cannot be rerolled;
- locked slots cannot be rerolled;
- past slots cannot be rerolled.

If a slot has no roulette lines but has manual lines, reroll should be unavailable or should ask "Generate a roulette suggestion for this meal?".

MVP recommendation:

- unavailable unless at least one roulette line exists or the slot is empty.

### Undo

Undo snapshot must capture:

- slot `planning_state`;
- all lines in affected slots;
- legacy mirror fields if retained.

Do not snapshot only direct `dish_id`/`recipe_id`.

---

## Shopping

Shopping list generation must include all dish lines in eligible meal slots.

Eligible:

- slot `planning_state = open`;
- slot status `planned`;
- line has recipe;
- date within requested window.

Excluded:

- `do_not_plan` slots;
- skipped/eaten/leftover slots as today;
- lines without recipe unless product says ingredient-less dishes are allowed.

`Needed for` should group by meal slot first, then line:

```text
Needed for
  Tue 14 Jul · Dinner
    Pasta alla Norma
    Green salad
```

Do not duplicate the date heading for every line in the same meal.

---

## Analytics and Composition Charts

The idea is good and fits the current recipe composition chart.

Add composition analytics at:

- meal slot level;
- day level;
- week level.

### Important data issue

Current `food_group_weights` are normalized per recipe. You cannot accurately aggregate meal/day/week charts by simply averaging recipe percentages.

Required for accurate aggregation:

- either compute aggregation directly from recipe ingredient lines;
- or extend computed traits to include absolute reference amounts:

```json
{
  "food_group_grams": {
    "carbohydrate": 500.0,
    "vegetable": 250.0
  },
  "total_trait_grams": 750.0
}
```

Recommended initial approach:

- extend trait computation to include `food_group_grams` and `total_trait_grams`;
- use those values to aggregate meal/day/week composition;
- keep `food_group_weights` for display compatibility.

Aggregation:

```text
meal = sum grams from all lines in slot
day = sum grams from all eligible meal slots on date
week = sum grams from all eligible meal slots in plan
weights = grams / total grams * 100
```

Threshold display:

- show groups `>= 10%`;
- group smaller groups as `Other`;
- keep the same accessible legend/list pattern as recipe chart.

UI placements:

- meal card expanded section: compact meal composition chart;
- day header or day summary: small day composition indicator;
- week page top summary: week composition chart with target context.

MVP recommendation:

- implement meal-level chart first;
- add day/week charts once aggregate API is stable.

Do not block composable meal MVP on day/week analytics if it grows too large.

---

## Frontend UX Requirements

## Plan Week / Today Cards

Each meal slot card should show:

- compact title using title rules above;
- status badges;
- lock/manual/roulette indicators;
- list of lines when expanded or in the card body;
- `Why this meal?` attached to roulette lines/package only;
- `+ Add dish` button when slot is not locked, not past, not `do_not_plan`;
- `Do not plan` action for future open slots;
- `Reopen` action for `do_not_plan` slots.

Line display:

```text
Pasta alla Norma                  Roulette · Main
Green salad                       Manual · Side     [Remove]
Fruit crumble                     Manual · Dessert  [Remove]
```

## Assignment Control

Replace "clear assignment" dropdown behavior with:

- line remove button;
- slot-level `Do not plan`;
- explicit Add/Replace modes.

Default empty slot:

- show one search/select assignment control;
- after selection, turn it into a line row and show `+ Add dish`.

Second and later lines:

- always removable;
- never use a blank dropdown option for clearing.

## Filtering

Dish selector should support role filters:

```text
All | Main | Centerpiece | Side | Dessert
```

Filtering source:

- `Main`: `meal_composition = main_dish`;
- `Centerpiece`: `meal_composition = simple_dish`, `simple_dish_part = centerpiece`;
- `Side`: `meal_composition = simple_dish`, `simple_dish_part = sidedish`;
- `Dessert`: `meal_composition = dessert`.

Keep search across all filters.

## Titles and Breadcrumbs

Do not force all dish names into the compact title.

Use:

- one line: dish name;
- simple pair: `Centerpiece with Side`;
- multiple: `Primary + N more`.

Full detail/list surfaces show all names.

## Accessibility

- Add-line button has clear label: `Add dish to dinner`.
- Remove buttons include dish names: `Remove Green salad`.
- Source badges are text, not color-only.
- Charts include accessible text lists.
- Do not rely on drag/drop for ordering; if ordering is implemented, provide buttons or menus.

---

## Tests

## Backend

Add tests for:

1. Migration backfills existing one-dish meal plan items into one line.
2. Meal slot can contain multiple lines.
3. `do_not_plan` prevents generate week and reroll.
4. Manual line add does not create roulette selection reasons.
5. Roulette main assignment creates one roulette line.
6. Roulette simple-pair assignment creates centerpiece + side lines.
7. Reroll replaces roulette lines but preserves manual extras.
8. Shopping includes all lines in a slot and excludes `do_not_plan`.
9. MealPlanItemPublic returns `title` and `lines`.
10. Undo restores all lines and planning state.
11. Weekly target counting does not double-count manual extras unless explicitly intended.
12. Meal composition aggregation uses grams, not equal-weight average percentages.

## Frontend

Add tests for:

1. Empty slot shows one assignment control.
2. After selecting a dish, `+ Add dish` appears.
3. Adding a second line renders both lines.
4. Removing a line removes only that line.
5. `Do not plan` shows `Not planning` and disables add/reroll.
6. Role filter limits dish options.
7. Catalog Plan For defaults to add, not replace.
8. Existing roulette line shows `Why this meal?`; manual line does not.
9. Multi-line title uses `Primary + N more`.
10. Meal composition chart renders accessible legend.

## E2E / Visual QA

Capture:

- empty meal slot;
- generated main dish;
- generated simple pair;
- generated meal with manual dessert added;
- do-not-plan slot;
- mobile add-line flow;
- meal-level composition chart.

Widths:

- 375 px;
- 390 px;
- 1440 px.

---

## Implementation Slices

### Slice 1 — Data Model and API Foundations

- Add `meal_plan_item_dishes`.
- Add `planning_state`.
- Backfill existing assignments.
- Add line schemas and serializers.
- Preserve legacy fields as primary-line mirrors.
- Add add/update/delete line endpoints.
- Add do-not-plan/reopen endpoints.

### Slice 2 — Manual Multi-Line Planning

- Update Plan Week/Today UI to render lines.
- Add `+ Add dish`.
- Add remove line.
- Add role filters.
- Update catalog Plan For to add rather than silently replace.
- Update shopping to include all lines.

### Slice 3 — Roulette Composition

- Extend candidates with meal composition.
- Generate either one main or one centerpiece+side pair.
- Store roulette lines and reasons.
- Update reroll/undo.
- Preserve manual extras.

### Slice 4 — Analytics

- Add aggregate grams to trait computation or direct aggregation service.
- Add meal-level composition chart.
- Add day/week charts if still small enough; otherwise schedule a later phase.

---

## Decisions Locked By This Spec

- A meal slot can contain any number of dish lines.
- Roulette creates either one main dish or one simple pair.
- Manual additions are unlimited.
- `Do not plan` is a slot-level planning state, not a skipped meal.
- Remove line replaces "clear assignment" for existing lines.
- Catalog Plan For must not silently replace existing meals.
- Ratings remain slot-level for MVP.
- Leftovers remain slot-level for MVP.
- Weekly targets should count meal slots/packages, not every extra line independently, unless later changed.

## Open Questions For Human Approval

1. Should `Do not plan` remove existing manual lines automatically, or ask first?
   - Recommendation: ask if lines exist; default to remove all.

2. Should roulette be allowed to add a side to an existing manual centerpiece?
   - Recommendation for MVP: no; roulette only controls empty slots or its own roulette package.

3. Should day/week analytics be required in the initial release or allowed to move to a later phase?
   - Recommendation: meal-level in the initial release; day/week later if implementation grows.

4. Should a simple pair title use "with" in all cases?
   - Recommendation: yes for compact English UI now; localization later.

5. Should manual extras affect weekly targets?
   - Recommendation: no for MVP weekly target satisfaction; yes for nutrition/composition analytics.

## Non-Goals

- No line-level ratings.
- No line-level leftovers.
- No drag/drop-only ordering.
- No deletion of legacy `meal_plan_items.dish_id` / `recipe_id` in the first migration.
- No automatic dessert roulette.
- No complex pairing AI beyond deterministic centerpiece+side candidate pairing and existing scoring.
