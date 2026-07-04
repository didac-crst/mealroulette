# Scheduler — family vectors and similarity

Authoritative rules for **Phase 8 / v0.5** automatic meal roulette. Implementation lives in `backend/mealroulette/services/scheduler/`. Product behaviour (reroll, generate week, scheduled job, Telegram) is in [CURSOR_ROADMAP.md](CURSOR_ROADMAP.md#phase-8---explainable-scheduler).

**Purpose:** similarity between dishes for history-aware roulette. **Not** used for weekly targets — those use dish **tags** only.

**Not in scope:** ML embeddings (see [SPECS.md §10](../SPECS.md#10-meal-similarity-logic)).

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
2. Else **default fallback:** **`100 g × quantity`** per count (household reference; configurable later in `planning_rules.rules_json` as `default_grams_per_count`, default `100`).

Do **not** skip count lines when no conversion exists — always apply step 2.

Record in selection/debug metadata when fallback was used (optional, for tests).

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

Example:

```json
{
  "pasta_family": 42.5,
  "tomato_family": 28.0,
  "cheese_family": 18.2,
  "onion_family": 11.3
}
```

### 1.6 Dynamic vocabulary

Vectors are **dicts**, not fixed-length arrays. Only families present in a dish appear. A new family in the ingredient seed adds a new key — existing dishes unchanged.

When comparing two dishes, iterate the **union of keys** (typically small).

---

## 2. Similarity between dishes

**Metric:** cosine similarity on sparse percentage dicts.

```python
cosine(a, b) = dot(a, b) / (||a|| × ||b||)
similarity_distance = 1 - cosine(a, b)   # 0 = identical, 1 = orthogonal
```

- Same computational cost as sparse Euclidean on dicts; chosen for scale safety if normalization drifts.
- Range: similarity_distance ∈ [0, 1] for non-negative vectors.

**Not used for:** weekly target checks (tags only).

### 2.1 History penalty

At roulette time, load **eaten** meals from `meal_history` in a recency window (default: 14 days before slot date; from `planning_rules`).

For each candidate dish **D** and slot date **S**:

1. **Same dish** as an eaten meal within `avoid_same_dish_within_days` → **hard exclude**.
2. Else compute `similarity_distance(vector(D), vector(eaten))` for each relevant eaten meal **E**.
3. **Penalty** = max over E of `recency_weight(E.date) × similarity_distance(D, E)`.

`recency_weight` decreases with days ago (e.g. 1.0 at 0 days, 0.5 at 7 days, 0.2 at 14 days — tunable in rules).

If `similarity_distance` ≥ `similarity_threshold` (default 0.75) for a recent meal → add human-readable reason: *“Similar to [dish] on [date] (shared families: …)”*.

---

## 3. Tags vs vectors (reminder)

| Mechanism | Role |
| --- | --- |
| **Tags** (`protein`, `carb`, `style`, `temperature`) | Weekly targets, min/max + tolerance, selection reasons |
| **Family vector** | Similarity to recent eaten meals only |
| **Seasonality** | Soft score per slot month (SPECS §11) |
| **Ratings** | Soft boost/penalty from household ratings |

---

## 4. Selection reasons (similarity)

When auto-picking, store JSON reasons including vector-related entries, e.g.:

```json
{
  "reasons": [
    "Not eaten in 24 days",
    "Low similarity to recent meals (max distance 0.32)",
    "Helps fish target (1/2 this week)"
  ],
  "vector_fallback_count_lines": 0
}
```

---

## 5. Tests (required)

- Mass, volume (with and without conversion), count with approved conversion, count with 100 g fallback.
- Pantry and `min_vector_grams` exclusion.
- L1 normalize sums to 100.
- Cosine: identical vectors → distance 0; orthogonal → distance 1.
- New family key does not break comparison with old dishes.
- Same-dish hard exclude in window.

---

## 6. Related docs

- [SPECS.md §10–12](../SPECS.md#10-meal-similarity-logic) — product-level scheduler design
- [CURSOR_ROADMAP.md § Phase 8](CURSOR_ROADMAP.md#phase-8---explainable-scheduler) — deliverables and API
- [BACKLOG.md](BACKLOG.md) — v0.5 checklist
