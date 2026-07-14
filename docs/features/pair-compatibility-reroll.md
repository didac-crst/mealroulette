# Pair Compatibility and Reroll Memory

## Document metadata

- **Purpose:** Define how composable meal pairs are validated, scored, explained, and rerolled.
- **Authority:** Canonical for centerpiece/side pair compatibility and reroll-exclusion semantics; base scheduler vector math remains in [scheduler.md](scheduler.md).
- **Status:** Approved next-phase specification.
- **Update when:** Pair scoring, candidate rejection, reroll history, or "Why this meal?" semantics change.

---

## Problem

Composable meals introduced valid meal-slot structures:

- one `main_dish`; or
- one `centerpiece` plus one `sidedish`.

That is necessary but not sufficient. A centerpiece and side can each be individually valid while forming a poor meal together.

Observed bad examples:

| Centerpiece | Side | Problem |
| --- | --- | --- |
| Grilled sardines | Tomato with tuna | Duplicate fish protein |
| Tuna steak | Tomato with tuna | Repeated tuna |
| Fish fillet | Tomato with tuna | Fish plus fish |
| Grilled sausages | Tomato with tuna | Competing animal proteins |
| Baked beans | Steamed green beans | Repetitive bean family |
| Zucchini omelette | Grilled eggplant | Valid, but may lack contrast or carb depending on context |

The architectural issue is that pair validity is currently too close to:

```text
centerpiece is valid AND side is valid
```

The scheduler must instead score the composed meal as one candidate:

```text
dish suitability + pair compatibility + whole-meal completeness
```

## Goals

- Prevent obviously bad centerpiece/side combinations.
- Preserve explainable, rule-based scheduler behavior.
- Keep generation fast enough for interactive use with a large simple-dish catalog.
- Improve reroll so it does not cycle through already-seen alternatives.
- Store pair-level reasons that can appear in "Why this meal?" and in scheduler debug output.

## Non-Goals

- Do not turn MealRoulette into a nutrition tracker.
- Do not use ML embeddings for core pair compatibility.
- Do not add line-level ratings or line-level leftovers.
- Do not implement per-component locking in this phase unless already present.
- Do not implement full day/week nutrition analytics in this phase.
- Do not redesign manual swap as a dish-line swap; swap remains a meal-slot/package operation.

Food-group and ingredient percentages are composition heuristics, not nutritional truth.

---

## Scheduler policy separation

Week generation, historical cooldown, and reroll memory are **three separate policies**. Do not conflate them.

| Policy | Purpose | Scope | Default / config |
| --- | --- | --- | --- |
| **Week structure** | Keep the intended mix of complete mains vs composed pairs across the planning week | Generate week (and structure-aware reroll when at composed max) | `composed_meals_per_week` min 4 / max 7; neutral share 60% main / 40% composed — see [scheduler.md](scheduler.md) |
| **History cooldown** | Avoid repeating dishes or overly similar meals across weeks | Eaten history + planned meals in temporal windows | `avoid_same_dish_within_days` 21; `avoid_similar_meals_within_days` 14; `history_window_days` 14 — planning rules |
| **Reroll seen memory** | Prevent `A → B → A` while editing **one slot** in the current planning interaction | Per meal-plan item, short-lived | Stored in `reroll_history_json`; not long-term taste memory |

### History cooldown (planning memory)

- **Same dish ID:** hard exclusion within `avoid_same_dish_within_days` (default **21 days**). After ~3 weeks the same dish may appear again. Use **28 days** if the product goal is roughly monthly variety.
- **Similar meals:** soft penalty within `avoid_similar_meals_within_days` (default **14 days**).
- **Pair-combination cooldown** (e.g. same centerpiece+side for 21–28 days) is **not** implemented in Phase 14. Add separately if pair repetition remains noticeable despite dish-level cooldown.

### Reroll seen memory (interaction memory)

- Prevents cycling through already-seen alternatives **for the slot being edited**.
- Must **not** persist as permanent taste memory and must **not** carry across planning weeks.
- Resets when: week regenerated; slot manually assigned; user **Start over**; item deleted; **plan week is before the current planning week**; **slot date is in the past**.
- May persist across browser refresh **only** while the slot remains today/future in the current or a future planning week.

Reroll can feel pair-heavy when many pair combinations exist. That is a separate product choice from week structure: “show many reroll alternatives” vs “reroll preserves weekly balance more strictly”. Phase 14 keeps generation structure-strict and reroll looser except when the week is already at composed max.

---

## Meal Candidate

A meal candidate is the unit scored by the scheduler.

It can be:

- a single main dish candidate; or
- a composed candidate containing one centerpiece line and one side line.

For composed meals, pair compatibility and whole-meal completeness are scored before the candidate can be selected.

## Primary Ingredients

Primary ingredients are the canonical ingredients that define a recipe's identity.

Initial derivation:

- include ingredients at or above 20% of recipe reference grams;
- always include the top two non-trivial ingredients when the recipe has usable grams;
- exclude trivial ingredients below `vector_min_grams`;
- exclude pantry/flavoring ingredients such as salt, water, oil, vinegar, garlic, herbs, and spices unless they are unusually dominant.

Use canonical ingredient IDs and ingredient family IDs, not display names.

## Dominant Protein and Dominant Carb

Use computed traits where available:

- `dominant_protein`;
- `dominant_carb`;
- food-group weights;
- ingredient family vector.

When traits are missing, fall back conservatively:

- no hard rejection unless canonical ingredient or family overlap is clear;
- apply lower confidence penalties instead of inventing protein/carb categories.

## Simple Dish Semantic Role

Keep existing persisted fields:

- `meal_composition`;
- `simple_dish_part`.

Add or derive a scheduler-facing role for scoring:

| Role | Meaning |
| --- | --- |
| `protein_centerpiece` | Centerpiece dominated by fish, meat, egg, dairy, tofu, or similar protein |
| `carb_centerpiece` | Centerpiece dominated by pasta, rice, potato, bread, grain, or similar carb |
| `vegetable_centerpiece` | Centerpiece dominated by vegetables |
| `legume_centerpiece` | Centerpiece dominated by beans, lentils, chickpeas, peas |
| `mixed_centerpiece` | No clear single dominant group |
| `protein_side` | Side with a meaningful protein identity |
| `carb_side` | Potato, rice, bread, grain, pasta, or similar side |
| `vegetable_side` | Cooked vegetable side |
| `salad_side` | Fresh vegetable/salad side |
| `soup_side` | Soup side |
| `bread_side` | Bread or toast side |
| `sauce_or_condiment` | Not enough to complete a meal by itself |

This role may be computed from recipe traits in the first implementation. Persist it only if tests show a need for human override.

---

## Pair Hard Rejections

Reject a centerpiece/side pair when any hard rule matches.

## Same Dominant Canonical Ingredient

Reject when primary canonical ingredients overlap.

Examples:

- tuna steak + tomato with tuna;
- aubergine centerpiece + grilled aubergine;
- potato tortilla + potato salad.

Do not reject for trivial overlap such as salt, oil, water, garlic, or herbs.

## Duplicate Dominant Protein

Reject when both dishes have the same dominant protein family.

Examples:

- sardines + tomato with tuna;
- tuna steak + tomato with tuna;
- fish fillet + tuna salad;
- egg centerpiece + egg-heavy side.

Fish species may be distinct canonical ingredients, but they still conflict at the dominant protein family level.

## Competing Animal Proteins

Reject or strongly penalize pairings where both dishes present animal protein as a principal identity.

Initial rule:

- reject fish + fish;
- reject meat + fish;
- reject meat + meat when both are primary;
- reject egg + egg;
- penalize egg + meat/fish unless the side's protein share is low.

The goal is not vegetarian doctrine; it is avoiding two main proteins disguised as a side.

## Excessive Ingredient-Family Overlap

Reject when both dishes are primarily from the same ingredient family and the side does not add meaningful contrast.

Examples:

- baked beans + steamed green beans;
- lentils + chickpea salad;
- tomato stew + tomato salad.

Initial threshold:

- if one shared family appears in the primary-family set of both dishes, reject when no different major family appears in the side;
- otherwise apply a soft penalty.

## Invalid Side Identity

Reject sides whose derived role is `sauce_or_condiment` unless the centerpiece already forms a complete meal and the product explicitly allows condiment-style additions.

Reject two soups or two cold salad-style dishes when both are the primary structure of the meal.

---

## Pair Soft Scoring

For pairs that pass hard rejections, compute a compatibility adjustment.

Suggested structure:

```text
pair_score =
  base_centerpiece_score
+ side_weight * base_side_score
+ complementarity_bonus
- dominant_ingredient_overlap_penalty
- dominant_family_overlap_penalty
- duplicate_group_penalty
- style_overlap_penalty
- cooking_method_overlap_penalty
- poor_balance_penalty
```

Initial defaults:

| Factor | Direction | Notes |
| --- | --- | --- |
| `side_weight` | `0.25` | Keep side from dominating the meal score |
| Primary canonical ingredient overlap | hard reject | Except trivial ingredients |
| Dominant protein overlap | hard reject | Fish+fish and tuna+tuna must fail |
| Primary family overlap | reject or strong penalty | Depends on side contrast |
| Same style/cooking method | small penalty | Only when reliable data exists |
| Poor meal balance | penalty | Heuristic, not nutrition scoring |

Weights must be covered by table-driven examples, not tuned only by screenshots.

---

## Positive Complementarity

The scheduler should reward sides that complete the centerpiece.

Initial matrix:

| Centerpiece role | Prefer | Avoid |
| --- | --- | --- |
| `protein_centerpiece` | `vegetable_side`, `salad_side`, `carb_side` | `protein_side` |
| `carb_centerpiece` | `vegetable_side`, `salad_side`, light `protein_side` | `carb_side` when carb-heavy |
| `vegetable_centerpiece` | `protein_side`, `carb_side` | another low-substance vegetable side |
| `legume_centerpiece` | `carb_side`, `vegetable_side`, `salad_side` | `legume_centerpiece`, legume-heavy side |
| `mixed_centerpiece` | side with the missing major group | duplicate dominant family |

Examples of preferred combinations:

| Centerpiece | Good side |
| --- | --- |
| Grilled sardines | tomato salad, roasted vegetables, potatoes |
| Sausages | potatoes, cabbage, grilled vegetables |
| Omelette | green salad, tomato salad, bread |
| Baked beans | rice, roasted vegetables, bread |
| Pasta centerpiece | green salad, vegetable soup |
| Fish fillet | potatoes, rice, vegetable side |

---

## Whole-Meal Completeness

After combining centerpiece and side traits, evaluate the meal package.

Heuristics:

- penalize if one food group dominates the combined grams too heavily;
- penalize if combined meal has fewer than two meaningful food groups;
- penalize if protein-heavy centerpiece plus protein-heavy side exceeds a high protein-share threshold;
- penalize if carb-heavy centerpiece plus carb-heavy side exceeds a high carb-share threshold;
- reward meals that combine protein/carb/vegetable groups in a practical way.

Do not display this as health scoring. Reasons should use household language:

- "Adds a vegetable side";
- "Balances a fish centerpiece with potatoes";
- "Avoids repeating tuna in the same meal".

---

## Reroll Memory

## Problem

Current reroll behavior can exclude only the current result:

```text
A -> reroll -> B -> reroll -> A
```

This is compliant with "exclude current dish" but poor product behavior.

## Required Reroll Behavior

```text
initial: A
reroll 1: exclude {A} -> B
reroll 2: exclude {A, B} -> C
reroll 3: exclude {A, B, C} -> D
```

For composed meals, history stores combinations, not only individual dishes:

```text
(sardines_id, tomato_tuna_id)
(fish_fillet_id, tomato_tuna_id)
(tuna_steak_id, tomato_tuna_id)
```

Normalize combination keys by line role and dish ID so equivalent ordering does not bypass exclusion.

## Persistence

Preferred implementation:

- backend-side reroll history stored on the meal plan item or in a small related table;
- reset when the week is regenerated;
- reset when the slot is manually assigned;
- reset when the user explicitly chooses "Start over";
- reset when the plan item is deleted;
- reset when the **plan week is before the current planning week** or the **slot date is before today** (stale interaction memory cleanup on plan load);
- keep across browser refreshes while the slot remains editable in the current or a future planning week.

Acceptable first implementation if backend persistence is too large:

- frontend session memory per plan item;
- backend still rejects the immediate current combination;
- document that refresh resets history.

Backend persistence is preferred because scheduled or multi-device use should not silently cycle.

## Exhaustion

When all suitable candidates have been seen:

```text
You've seen all suitable alternatives.
[Start over] [Choose manually]
```

Do not silently cycle back to the original combination.

API responses should distinguish:

- success with selected meal;
- exhausted suitable alternatives;
- slot not eligible for reroll.

---

## Reroll Semantics for Composed Meals

Meal-level reroll replaces the roulette-generated meal package.

Rules:

- preserve manual lines;
- replace roulette-sourced lines;
- never change locked or past slots;
- never fill `do_not_plan` slots;
- if component locking is added later, preserve locked components and reroll only unlocked roulette lines.

Do not implement "replace only the bad component" in this phase. It is a future enhancement once pair rejection reasons are reliable.

---

## Swap Semantics for Composed Meals

Swap is currently a meal-level action. After composable meals, it must continue to swap the whole meal package, not one dish line.

## Required Swap Behavior

- the chooser must show target meal slots, not individual dish lines;
- each target option must display the whole menu for that slot;
- a composed target should display all lines, for example `Buttered Pasta + Greek Salad`;
- a main-dish target should display its single main dish;
- a `Do not plan` target should be displayed as a slot state and should either be excluded or explicitly labelled according to existing swap eligibility rules;
- selecting a target swaps the full slot assignment package between the two meal slots.

The full package includes:

- all meal dish lines;
- line order/position;
- roles;
- source/manual vs roulette markers;
- recipe selections;
- selection reasons;
- legacy mirror fields while they still exist;
- slot planning state where the existing product semantics require it.

Swap must not show only the first dish in a composed meal. Showing only one dish creates a false target and makes users think they are swapping a single component.

## Eligibility

Preserve existing safety rules:

- locked slots cannot be swapped unless existing behavior already allows it;
- past slots cannot be swapped unless existing behavior already allows it;
- `do_not_plan` slots must not be accidentally converted into planned slots without explicit behavior;
- manual extras must move with their meal package.

If the existing API only swaps `dish_id`, `recipe_id`, and direct item fields, update it to swap line packages as well.

Do not implement component-level swap in this phase. A future component-level swap would need a distinct UI label such as `Swap side`, not the current meal-level `Swap`.

---

## Explainability

Selection reasons should include pair-level reasons when a composed meal is selected.

Examples:

```text
Why this meal?
- Sardines provide the main protein.
- Boiled potatoes add a carb side without repeating fish.
- Helps satisfy the fish target this week.
- Not similar to nearby planned meals.
```

Internal debug output should expose rejected combinations and reason codes:

```text
Rejected Tomato with tuna:
- duplicate_dominant_protein: fish
- shared_primary_ingredient: tuna
```

Normal users do not need to see every rejected option, but tests and scheduler debug tooling should be able to inspect reason codes.

## Reason Codes

Initial reason-code vocabulary:

| Code | Meaning |
| --- | --- |
| `shared_primary_ingredient` | Both dishes share a primary canonical ingredient |
| `duplicate_dominant_protein` | Both dishes use the same dominant protein family |
| `competing_animal_proteins` | Both dishes are principal animal-protein dishes |
| `primary_family_overlap` | Principal ingredient family repeats |
| `invalid_side_identity` | Side is not substantial enough for a pair |
| `positive_complementarity` | Side complements centerpiece role |
| `whole_meal_balance` | Combined meal has practical food-group balance |
| `reroll_seen_combination` | Candidate already shown in current reroll session |
| `reroll_exhausted` | No suitable unseen alternatives remain |

---

## Implementation Slices

## Slice 1 - Diagnostics and Trait Inputs

- Add helpers to derive primary ingredient IDs and family IDs from recipe lines.
- Derive scheduler simple-dish semantic roles from computed traits.
- Add tests for primary-ingredient extraction and role derivation.
- Keep all derivation on the fly unless profiling proves it is too slow.

## Slice 2 - Pair Hard Rejections

- Apply hard pair constraints before candidate shortlist scoring.
- Ensure bad screenshot examples are rejected or explicitly penalized according to this spec.
- Add reason codes for every rejection.
- Preserve bounded shortlist performance.

## Slice 3 - Pair Compatibility Score

- Add complementarity matrix.
- Add whole-meal completeness heuristics.
- Generate pair-level "Why this meal?" reasons.
- Keep weighted randomness among top valid candidates; do not always choose the top score.

## Slice 4 - Reroll Memory

- Add reroll seen-combination tracking.
- Exclude current and previously seen combinations.
- Add exhaustion API response and UI state.
- Reset history on generate week, manual assignment, explicit start-over, and item deletion.

---

## Acceptance Tests

## Pair Compatibility

Table-driven backend tests:

| Pair | Expected |
| --- | --- |
| Grilled sardines + tomato with tuna | reject: `duplicate_dominant_protein` |
| Tuna steak + tomato with tuna | reject: `shared_primary_ingredient` and/or `duplicate_dominant_protein` |
| Fish fillet + tomato with tuna | reject: `duplicate_dominant_protein` |
| Grilled sausages + tomato with tuna | reject or strong penalty: `competing_animal_proteins` |
| Baked beans + steamed green beans | reject or strong penalty: `primary_family_overlap` |
| Zucchini omelette + grilled eggplant | valid, lower score if no carb/contrast |
| Grilled sardines + tomato salad | valid, positive complementarity |
| Grilled sardines + boiled potatoes | valid, positive complementarity |

## Reroll

- Initial result A, reroll returns B, next reroll must not return A.
- Composed reroll history excludes complete combinations.
- Reroll preserves manual extras.
- `do_not_plan`, locked, and past slots cannot reroll.
- Exhaustion returns explicit exhausted state and does not cycle.
- Start-over clears reroll history.
- Stale reroll history clears when the plan week is before the current planning week or the slot date is in the past.

## Swap

- Swap target list displays complete meal-slot menus, not only the first dish line.
- Swapping a composed meal with another composed meal exchanges all dish lines and metadata.
- Swapping a composed meal with a main-dish meal exchanges the whole meal package in both directions.
- Manual extras move with the swapped meal package.
- Selection reasons and roulette/manual source markers remain attached to the moved lines.
- Locked, past, and `do_not_plan` eligibility follows existing slot-level swap rules.
- No component-level swap is exposed under the meal-level `Swap` action.

## Explainability

- Selected composed meals include at least one pair-level reason when a pair is selected.
- Rejected candidate reason codes are available to backend tests/debug output.
- User-facing reasons do not use nutrition-tracker language.

## Performance

- Large simple-dish catalog generation remains interactive.
- Pair compatibility must run after candidate preselection or with efficient precomputed trait summaries.
- Avoid N+1 recipe/ingredient loading when scoring pairs.
- Add a deterministic non-wall-clock test proving the number of pair evaluations is bounded.

---

## Future Enhancements

- Persist human-overridable `simple_dish_role` if computed roles are not enough.
- Component-level reroll: keep the good component and replace the incompatible one.
- Day/week composition analytics.
- Pair compatibility admin diagnostics page.
- Household-specific pair preferences once households/workspaces exist.
