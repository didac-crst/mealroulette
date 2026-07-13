# Scheduler — family vectors and similarity

## Document metadata

- **Purpose:** Family-vector similarity and how it relates to weekly target matching.
- **Authority:** Canonical for scheduler vector math; weekly target semantics also in [computed-traits.md](computed-traits.md) and [meal-composition.md](meal-composition.md).
- **Status:** Living — update when scheduler scoring changes.
- **Update when:** `targets.py` or neighbour/scoring rules change.

---

Authoritative rules for **Phase 8 / v0.5** automatic meal roulette (extended in Phase 11 for trait-based targets). Implementation lives in `backend/mealroulette/services/scheduler/`. Product behaviour (reroll, generate week, scheduled job, Telegram) is in [CURSOR_ROADMAP.md](../CURSOR_ROADMAP.md#phase-8---explainable-scheduler).

**Purpose:** similarity between dishes for history-aware roulette. **Weekly targets** use main-recipe **computed traits** first (`fish`, `meat`, `pasta`, `rice`, `vegetarian`, …), with **curated style tags** as fallback for non-derivable classifications (e.g. `soup`). See `mealroulette.services.scheduler.targets`.

**Not in scope:** ML embeddings (see [SPECS.md §10](../../SPECS.md#10-meal-similarity-logic)).

---

## 1. Dish family vector

Built **on the fly** when the scheduler runs. Not stored in the database.

**Input:** main recipe ingredient lines + normalized `Ingredient` rows from the catalog.

**Output:** sparse dict `family → weight_pct` where weights are **L1-normalized percentages** (sum = 100). Absent keys = 0.

### 1.1 Ingredient line → grams

Each recipe line is converted to a **reference mass in grams**. This is approximate — only for similarity, not shopping lists.

| Unit dimension | Conversion rule |
| --- | --- |
| **Mass** | Convert to g using standard unit table (`mealroulette.services.quantities`). |
| **Volume** | Convert to ml when a path exists; then treat **1 ml = 1 g**. If no volume conversion exists, treat raw quantity as grams equivalent (**1 unit = 1 g** per ml fallback step). |
| **Count** | See [§1.2 Count → grams](#12-count--grams). |

If quantity is missing or zero, skip the line.

### 1.2 Count → grams

Priority order:

1. **Approved** ingredient-specific conversion where `from_unit` is `unit` (or count) and `to_unit` is `g` — use `quantity × factor`.
2. Else **default fallback:** **`100 g × quantity`** per count (household reference; configurable in `planning_rules.rules_json` as `default_grams_per_count`, default `100`).

Do **not** skip count lines when no conversion exists — always apply step 2.

### 1.3 Ingredient → family key

Map each line to a rollup key:

1. `ingredient.family` if set (preferred — from seed, e.g. `tomato_family`, `pasta_family`).
2. Else `ingredient.category` (e.g. `vegetable`, `meat`).
3. Else `ingredient.canonical_name` as last resort.

If no key after step 3, skip the line.

### 1.4 Lines excluded before rollup

Excluded lines do not contribute grams (keeps vectors sparse; negligible effect on similarity):

| Rule | Rationale |
| --- | --- |
| `ingredient.pantry_item == true` | Salt, oil, spices — not meal “shape”. |
| Converted mass **&lt; `min_vector_grams`** (default **5 g**) | Drops pinch-sized spices; same effect as ~0% after normalize. |

Configurable in `planning_rules.rules_json`:

```json
{
  "vector_min_grams": 5,
  "default_grams_per_count": 100
}
```

### 1.5 Rollup and normalize

1. Sum grams per family key.
2. **L1-normalize:** `weight_pct(f) = 100 × grams(f) / total_grams` (if `total_grams == 0`, empty vector).

### 1.6 Dynamic vocabulary

Vectors are **dicts**, not fixed-length arrays. Only families present in a dish appear. A new family in the ingredient seed adds a new key — existing dishes unchanged.

When comparing two dishes, iterate the **union of keys** (typically small).

---

## 2. Similarity between dishes

**Metric:** cosine similarity on sparse percentage dicts.

```python
cosine(a, b) = dot(a, b) / (||a|| × ||b||)
similarity_distance = 1 - cosine(a, b)   # 0 = identical, 1 = orthogonal
similarity = 1 - similarity_distance     # 1 = identical, 0 = orthogonal
```

- Range: `similarity_distance ∈ [0, 1]` for non-negative vectors.
- **Not used for:** weekly target checks (traits + style-tag fallback handle those).
- **Tags are not merged into the family vector.** Pasta vs rice similarity comes from overlapping ingredient families; weekly targets use computed traits from the main recipe, not the vector.

---

## 3. Temporal neighbours (similarity context)

Similarity is **not** eaten-history-only. At scoring time for slot **S**, build a neighbour list:

| Source | Included when | `source` label |
| --- | --- | --- |
| **Eaten meals** | `abs(S.date − E.date) ≤ avoid_similar_meals_within_days` | `eaten` |
| **Locked / manual / other assigned plan meals** | same window, same week plan | `planned` |
| **Slots already filled earlier in this generation attempt** | same window | `generated` |

The slot being filled is **excluded** from its own neighbour list.

**Temporal weight** uses **calendar distance**, symmetric for past and future:

```python
days_apart = abs(S.date - neighbour.date)
temporal_weight = max(0.2, 1.0 - days_apart / history_window_days)
```

Example: rerolling **Tue** with **Fri** locked to risotto → `days_apart = 3`. Planning **Thu** with similar dish on **Fri** → `days_apart = 1` → **stronger** penalty than a neighbour 4 days away.

### 3.1 Similarity penalty

For each candidate dish **D** and slot **S**:

1. **Same dish ID** as any meal in `avoid_same_dish_within_days` → **hard exclude** (eaten or planned).
2. Else for each neighbour **N** in the temporal window:
   - `similarity = 1 − similarity_distance(vector(D), vector(N))`
   - `penalty contribution = temporal_weight(|S.date − N.date|) × similarity`
3. **Penalty** = max contribution over neighbours (most similar close neighbour wins).

If `similarity ≥ similarity_threshold` (default **0.75**, meaning cosine ≥ 0.75) → selection reason: *“Similar to [dish] on [date] (shared families: …)”*.

If all neighbours are far (`min distance ≥ 0.45`) → reason: *“Good variety vs neighbouring meals …”*.

---

## 4. Sequential week generation

The generator fills slots **in calendar order** (Mon lunch → Mon dinner → …). Each pick sees:

| Signal | Aware of earlier picks in same run? |
| --- | --- |
| Weekly targets | Yes — via `assigned_dish_ids` |
| Same dish twice in week | Yes — hard block |
| Similarity penalty | Yes — via `generated` neighbours |
| Locked / manual meals | Yes — via `planned` neighbours |
| Eaten history | Yes — via `eaten` neighbours |

**Algorithm:** up to `plan_attempts` (default 50) full passes. Each pass fills all open slots in order; keep the pass with highest total score. Per slot: filter hard constraints → score → take top 5 → weighted random pick.

---

## 5. Traits, tags, and vectors (reminder)

| Mechanism | Role |
| --- | --- |
| **Computed traits** (main recipe) | Weekly targets (`fish`, `meat`, `pasta`, `rice`, `vegetarian`, …) |
| **Curated style tags** | Fallback for non-derivable targets (e.g. `soup`); temperature and legacy carb/protein tags where still used |
| **Family vector** | Similarity to temporal neighbours only |
| **Seasonality** | Soft score per slot month |
| **Ratings** | Soft boost from household ratings |

---

## 6. Roulette API and undo

| Endpoint | Behaviour |
| --- | --- |
| `POST /api/meal-plans/{id}/generate` | Fill all regenerable slots; preserve locked/manual/past |
| `POST /api/meal-plans/{id}/generate/details` | Same + warnings, variety assessment, scores |
| `POST /api/meal-plan-items/{id}/reroll` | Replace one slot (today/future, unlocked) |
| `POST /api/meal-plan-items/{id}/reroll/details` | Same + metadata |
| `POST /api/meal-plans/{id}/undo-roulette` | Restore **last** generate or reroll snapshot |

**Undo:** one level only. Before each generate/reroll, snapshot affected items (`dish_id`, `recipe_id`, `selection_reasons_json`, `manually_selected`) into `meal_plans.last_roulette_undo_json`. Undo restores and clears the snapshot.

**Variety assessment** (for UI review): per new assignment, nearest temporal neighbour + distance label (`very similar` … `very different`). No 2D embedding.

---

## 7. Meal swap (manual rebalance)

`POST /api/meal-plan-items/{id}/swap` with `{ "target_item_id": … }`.

**Pure exchange** of `dish_id`, `recipe_id`, and `selection_reasons_json` between two **planned** slots in the same week (today or future). No similarity checks, no target recalculation — manual rebalance only (same philosophy as leftovers and manual picks).

Lock flags stay on each slot; only the dishes move.

### 7.1 Plan from dish gallery

`POST /api/meal-plan-items/assign` with `{ "date", "meal_slot", "dish_id", "recipe_id?" }`.

Creates the meal-plan week if needed, assigns the dish to the chosen lunch/dinner slot (today or future), sets `manually_selected=true`, and clears auto `selection_reasons_json`. UI entry points: dish library card **Plan for…** and dish detail page.

---

## 8. Scheduled roulette (worker)

Configured in **`scheduler_settings`** (admin UI `/settings/scheduler`, API `GET/PUT /api/scheduler/settings`).

| Setting | Default | Meaning |
| --- | --- | --- |
| `enabled` | false | Worker runs job when true |
| `run_weekday` | 4 (Friday) | Local weekday to trigger |
| `run_time` | 18:00 | Local time (with `timezone`) |
| `target_week_offset` | 1 | 0 = this Mon–Sun, 1 = next week, etc. |
| `notify_telegram` | true | Broadcast after successful generate |
| `notify_planning_days` | 7 | Days of plan shown in Telegram HTML |

**Worker:** minute cron (same as daily Telegram reminder). `ScheduledRouletteService.run_scheduled()` skips unless `should_run_scheduled`: on the configured local weekday, at or after `run_time`, once per local calendar day.

**On trigger:** `get_or_create_plan(target_week)` → `generate_week` → optional **“New roulette”** HTML message to Telegram subscribers (reuses planning formatter).

**Manual:** `POST /api/scheduler/run-roulette` (admin) runs immediately regardless of schedule.

---

## 9. Selection reasons (example)

```json
{
  "reasons": [
    "Good variety vs neighbouring meals (min distance 0.52)",
    "Helps fish target (1/2 this week)"
  ],
  "score": 1.85,
  "similarity_distance_max": 0.52
}
```

---

## 10. Tests (required)

- Mass, volume, count conversions and vector normalize (see slice 2 tests).
- Temporal weight symmetry; closer neighbours penalize more.
- Future locked meals affect scoring.
- Sequential generation: later slot sees earlier pick as neighbour.
- Generate / reroll / undo API; swap exchange; Phase 8 acceptance API tests (`test_scheduler_acceptance.py`).
- Locked meals preserved; past slots blocked.

---

## 11. Related docs

- [SPECS.md §10–12](../../SPECS.md#10-meal-similarity-logic) — product-level scheduler design
- [CURSOR_ROADMAP.md § Phase 8](../CURSOR_ROADMAP.md#phase-8---explainable-scheduler) — deliverables and UI slices
- [BACKLOG.md](../BACKLOG.md) — shipment status
