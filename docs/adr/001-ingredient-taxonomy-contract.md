# ADR 001 — Ingredient taxonomy contract

## Document metadata

- **Purpose:** Durable decisions on ingredient granularity, aliases, and catalogue growth.
- **Authority:** Canonical for taxonomy contract; feature detail in [features/taxonomy-resolver.md](../features/taxonomy-resolver.md).
- **Status:** Accepted — frozen decision record.
- **Update when:** Only via a new ADR superseding this one.

**Status:** Accepted (July 2026)  
**Context:** Phase 9 catalogue expansion paused at ~627 proposal rows. Priority is a coherent ~500–600 ingredient active catalogue, not 2,000 partially reviewed entries.

## Decisions

### 1. Canonical granularity

Create separate canonical ingredients only when the distinction materially changes at least one of:

1. recipe compatibility;
2. substitution behaviour;
3. shopping behaviour;
4. dietary or allergen behaviour;
5. unit conversion;
6. preparation or cooking outcome.

**Default:** prefer one generic canonical (e.g. `onion`, `hake`, `salmon`, `parsley`, `thyme`) with forms handled as metadata or aliases—not separate canonical rows for every cut or locale name.

### 2. Aliases versus translations

- One alias maps to **exactly one** canonical ingredient after normalization.
- Regionally ambiguous terms (e.g. `abadejo`, `muslo de pollo`) are **not** shared exact aliases; use locale/context in resolver later.
- Cross-language names (`courgette` / `zucchini`) are aliases on a single canonical row.

### 3. Product form and preservation (metadata, not explosion)

Optional YAML/DB fields:

- `product_form`: `whole`, `fillet`, `steak`, `minced`, `grated`, `sliced`, `paste`, …
- `preservation`: `fresh`, `frozen`, `dried`, `canned`, `pickled`, `smoked`, `salted`, …

Separate canonical entries only when transformation creates a **distinct product** (tomato vs tomato paste, cod vs salt cod, quince vs quince paste).

### 4. Semantic food group vs culinary role

- **`food_group`**: biological/origin group for traits (vegetable, fish, fruit, fat, …).
- **`culinary_category`**: optional culinary role (condiment, sauce, stock_base, …) when it differs from family default.
- Validator must **not** require `food_group == family.food_group` when `culinary_category` is set.

### 5. Storage

- **`storage_class`**: `ambient`, `refrigerated`, `frozen`, `fresh_produce` (one default per ingredient for MVP).
- **`pantry_item`**: retained for backward compatibility; derived from `storage_class == ambient` for long-life items when not explicitly set.

Do not use `food_group: pantry` for real foods (canned tomato, dry pasta, spices). Use semantic `food_group` + `storage_class: ambient`.

### 6. Merge and deprecation

- Never delete active canonical IDs used in recipes without a redirect.
- Renames keep old canonical as **alias** on the surviving row (`deprecated_canonical_aliases` in seed metadata).
- Proposal rows merge into active via explicit mapping before promotion.

### 7. Catalogue freeze

No push toward 2,000 ingredients until recipe-driven evidence. MVP target: **500–600** reviewed active ingredients.

### 8. Review exceptions

Rows may carry:

```yaml
review_status: approved_exception
review_note: >
  Intentional modelling choice; do not re-flag in validation.
```

## Consequences

- Reconciliation script merges proposal + active seed under this contract.
- Validator flags blockers; `approved_exception` rows skip re-review.
- Import accepts `storage_class`, `culinary_category`, `product_form`, `preservation`.

### 9. Unit conversion approval

Three classes (see `mealroulette/data/conversion_policy.py`):

1. **Size estimates** (`unit`/`fillet`/`bunch`→`g`, etc.) — `confidence: approximate`, `approved: false`. Display estimates only; shopping uses approved conversions only.
2. **Herbs, citrus, aromatics** — same unless the pair is physically deterministic.
3. **Sheets / drained goods** — `product_form: sheet` for pastry; prefer volume exact pairs over mass estimates.

**May approve:** `tbsp→ml`, `tsp→ml`, `kg→g`, `l→ml` (and inverses).

**Do not approve:** `unit→g`, `bunch→g`, `sheet→g`, `fillet→g`, fruit→juice mass/volume estimates.

Apply: `python -m mealroulette.commands.apply_conversion_policy`
