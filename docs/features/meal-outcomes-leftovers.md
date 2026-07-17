# Meal Outcomes And Leftovers

## Document metadata

- **Purpose:** Optional meal outcome review, leftover batch inventory, use-soon hints, and planning/shopping integration.
- **Authority:** Feature specification for future Phase 17 product hardening.
- **Status:** Accepted design — implementation not started.
- **Update when:** Meal review semantics, leftover inventory, scheduler integration, or shopping-list behavior changes.

---

MealRoulette should remember what the household actually ate, what remains, and what should be used soon. The goal is to reduce future decisions and food waste, not to force users to maintain a warehouse ledger.

## Principles

- Review remains optional.
- `not reviewed` is a valid state indefinitely.
- Never infer that an unreviewed planned meal was eaten.
- Never create leftovers without explicit user confirmation.
- Closing or skipping the leftover prompt creates no leftover record.
- Every extra record should give the user an immediate benefit.
- The system must tolerate stale or incomplete leftover data.

## Meal Outcome Actions

Fast review prompt:

```text
What happened?
[Ate as planned]
[Ate something else]
[Ate leftovers]
[Skipped]
[Not now]
```

`Ate as planned`:

- updates actual meal history;
- improves repetition avoidance;
- may count toward actual weekly targets;
- may ask the optional leftover question.

`Skipped`:

- does not count as eaten;
- optional reason may help future scheduling;
- creates no leftover prompt.

`Ate something else`:

- records that the planned meal was not eaten;
- may optionally link another household dish, quick description, or unknown meal;
- creates no leftover from the skipped planned meal.

`Ate leftovers`:

- consumes portions from an existing leftover batch;
- satisfies the meal slot without adding recipe ingredients to shopping.

`Not now`:

- leaves the meal outcome unknown.

## Leftover Creation

After `Ate as planned`, show an optional secondary prompt:

```text
Any leftovers?
[No]
[1 portion]
[2 portions]
[3+]
[Custom]
```

If the user closes the prompt, chooses `No`, or skips the prompt, create no leftover batch.

There should also be a later entry point:

```text
Add leftovers
```

That entry point may suggest recent meals as sources up to a bounded lookback window. MealRoulette can keep long-term meal history, but the add-leftovers UI should emphasize recent relevant meals, not an infinite selector.

## Identity And Provenance

Leftovers are tracked primarily at dish/recipe level, not meal level.

The source meal plan item is optional provenance, not identity.

```text
leftover_batch
  -> dish_id
  -> recipe_id NULL
  -> source_meal_plan_item_id NULL
```

This allows:

- leftovers created manually after the fact;
- leftovers from unplanned cooking;
- leftovers from a known planned meal;
- tracking usable food without depending on a complete meal-review workflow.

## Data Model

```text
leftover_batches
- id UUID
- household_id
- dish_id
- recipe_id NULL
- source_meal_plan_item_id NULL
- created_by_user_id
- portions_total NUMERIC
- portions_reserved NUMERIC DEFAULT 0
- portions_consumed NUMERIC DEFAULT 0
- portions_discarded NUMERIC DEFAULT 0
- storage_location
    fridge
    freezer
- cooked_at NULL
- stored_at
- eat_before
- eat_before_source
    default
    user_set
- status
    available
    partly_consumed
    consumed
    discarded
    unknown
- notes NULL
- created_at
- updated_at
```

Default `eat_before` suggestions:

- fridge: stored date + 3 days;
- freezer: stored date + 1 month.

The user is responsible for confirming or changing `eat_before`. Wording should be "best to use by" or "use soon", not definitive food-safety advice.

## Leftover Inventory Page

Dedicated page:

```text
Leftovers
```

Views:

- Use soon;
- Fridge;
- Freezer;
- Unknown/stale;
- Consumed/discarded history.

Actions:

- Plan for lunch;
- Plan for dinner;
- Move to freezer;
- Mark consumed;
- Mark discarded;
- Edit portions;
- Edit eat-before date;
- Add leftovers.

## Reservations

Leftover portions should be reservable by planned meals.

Rules:

- A batch cannot be scheduled for more portions than unreserved availability.
- Planning reserves portions.
- Eating consumes reserved portions.
- Removing the planned leftover meal releases the reservation.
- Manual corrections remain possible.

This prevents the same two portions from being planned twice.

## Scheduler Integration

Leftover candidates are distinct from new-recipe candidates.

Scoring signals:

- eat-before urgency;
- available unreserved portions;
- meal-slot fit;
- fridge vs freezer;
- user willingness to auto-schedule leftovers;
- already planned elsewhere.

Example explanation:

```text
Chicken curry leftovers were selected because two portions are available and they should be used soon.
```

Users must be able to disable automatic leftover scheduling.

## Shopping Integration

If a meal slot is fulfilled by leftovers, the shopping list should not include the original recipe ingredients again.

Shopping UI example:

```text
Tuesday dinner
Chicken curry leftovers
No ingredients required
```

This is one of the highest-value reasons to track leftovers.

## Use-Soon Ingredient Hints

Do not build a full pantry ledger first.

Use a lighter model:

```text
ingredient_use_priorities
- id UUID
- household_id
- ingredient_id
- quantity_value NULL
- unit_id NULL
- use_by NULL
- priority
    normal
    soon
    urgent
- source
    manual
    shopping_leftover
    imported
- status
    active
    used
    discarded
- created_at
- updated_at
```

These are scheduling hints, not authoritative stock.

Example explanation:

```text
This dish uses spinach, which you marked as "use soon".
```

## Public Recipe Metrics

Only confirmed outcomes should feed public recipe quality signals.

Useful public metrics:

- unique households that adopted;
- unique households that confirmed eating;
- repeat-cook rate;
- post-meal ratings;
- planned-then-skipped rate;
- immediate reroll rate.

Do not treat unreviewed planned meals as eaten or skipped.

Do not reward users for pressing review buttons. The user-facing benefit of review is better planning, accurate leftovers, and less waste.

## Anti-Overfitting

Do not overlearn from one action.

Signal strengths:

| Signal | Meaning | Suggested weight |
| --- | --- | --- |
| Recipe rating | General preference | Strong |
| Repeated eating | Demonstrated preference | Strong |
| Manual selection | Current intent | Medium |
| Ate as planned | Acceptance | Weak/medium |
| Single skip | Context-specific | Weak |
| Repeated same-context skip | Suitability issue | Medium |
| Immediate reroll | Temporary rejection | Weak |
| Discarded leftovers | Possible portion/preference issue | Medium after repetition |

## Recommended Implementation Sequence

Phase 17A — Review value redesign:

- optional fast outcome prompt;
- `ate something else`;
- clear unknown vs skipped;
- explain scheduler benefit.

Phase 17B — Leftover batches:

- explicit leftover creation;
- later add-leftovers entry point;
- portions, fridge/freezer, eat-before;
- inventory page.

Phase 17C — Planning and shopping integration:

- reservation logic;
- schedule leftovers;
- exclude ingredients from shopping;
- "Why this meal?" reasons.

Phase 17D — Notifications:

- expiring fridge leftovers;
- actionable plan/freeze/consume/discard controls;
- channel preferences.

Phase 17E — Use-soon ingredient hints:

- lightweight canonical ingredient hints;
- scheduler boosts;
- optional quantity/date.

## Acceptance Criteria

- Closing a leftover prompt creates no leftover batch.
- Users can add leftovers later from recent meals or by manually choosing dish/recipe.
- Leftovers are tracked at dish/recipe level with optional source meal provenance.
- Users can set or override `eat_before`.
- Fridge and freezer have sensible default `eat_before` suggestions.
- Planning cannot reserve unavailable leftover portions.
- Shopping excludes ingredients for leftover-fed meal slots.
- Unreviewed meals remain outcome-unknown forever.
